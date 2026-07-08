"""
智能家居 YOLO 识别服务
功能：图片/摄像头读取 -> YOLOv8目标检测 -> 结果保存 -> Web页面展示 -> 小组接口对接 -> 可选硬件联动
适用：香橙派 / Linux / Windows 开发机

作者角色：YOLO识别负责人

重要对接说明：
1. 与硬件组对接灯光/门禁/蜂鸣器等控制，请看 notify_hardware_if_needed() 函数。
2. 与后端/数据库组对接识别历史，请看 save_detection_to_db() 函数和 /api/history 接口。
3. 与GUI组对接展示，请看 templates/index.html、static/app.js 以及 API 接口。

"""

import json
import os
import platform
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import cv2
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

try:
    from ultralytics import YOLO
except Exception as exc:  
    YOLO = None
    YOLO_IMPORT_ERROR = exc
else:
    YOLO_IMPORT_ERROR = None


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """读取配置文件。没有配置文件时使用默认配置。"""
    default_config = {
        "server": {"host": "0.0.0.0", "port": 5000, "debug": False},
        "model": {
            "path": "weights/best.pt",
            "fallback_model": "yolov8n.pt",
            "confidence": 0.35,
            "imgsz": 640,
            "device": "cpu"
        },
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "warmup_frames": 5
        },
        "save": {
            "raw_dir": "images",
            "result_image_dir": "results/images",
            "json_dir": "results/json",
            "txt_dir": "results/txt",
            "database": "results/detections.db"
        },
        "hardware": {
            "enabled": False,
            "timeout_seconds": 2,
            "trigger_rules": [
                {
                    "name": "检测到灯泡后开灯",
                    "classes": ["light_bulb"],
                    "min_confidence": 0.40,
                    "method": "POST",
                    "endpoint": "http://127.0.0.1:8000/api/v1/devices/light/control",
                    "payload": {"on": True, "brightness": 80, "source": "yolo"}
                }
            ]
        }
    }

    if not CONFIG_PATH.exists():
        return default_config

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        user_config = json.load(f)

    # 简单递归合并，避免用户只写部分配置导致缺字段
    def merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(a)
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(result.get(k), dict):
                result[k] = merge(result[k], v)
            else:
                result[k] = v
        return result

    return merge(default_config, user_config)


CONFIG = load_config()

RAW_DIR = BASE_DIR / CONFIG["save"]["raw_dir"]
RESULT_IMAGE_DIR = BASE_DIR / CONFIG["save"]["result_image_dir"]
JSON_DIR = BASE_DIR / CONFIG["save"]["json_dir"]
TXT_DIR = BASE_DIR / CONFIG["save"]["txt_dir"]
DB_PATH = BASE_DIR / CONFIG["save"]["database"]
UPLOAD_DIR = BASE_DIR / "uploads"

for directory in [RAW_DIR, RESULT_IMAGE_DIR, JSON_DIR, TXT_DIR, UPLOAD_DIR, DB_PATH.parent]:
    directory.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 上传图片最大 20MB

_model = None
_model_lock = Lock()


# =============================
# 数据库：保存识别历史
# =============================
def init_db() -> None:
    """初始化 SQLite 数据库。用于存储识别历史，方便GUI/后端查询。"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_image TEXT NOT NULL,
                result_image TEXT NOT NULL,
                json_file TEXT NOT NULL,
                txt_file TEXT NOT NULL,
                object_count INTEGER NOT NULL,
                objects_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_detection_to_db(data: Dict[str, Any]) -> int:
    """
    保存识别记录到本地 SQLite。

    [对接点-后端/数据库组]
    如果你们统一使用 MySQL、MongoDB、云数据库或别的后端，
    可以在这里把 data 同步发给后端，或者改为直接写入你们的数据库。
    data 中包含：时间、原图文件名、结果图文件名、json文件名、txt文件名、识别目标列表。
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO detections
            (created_at, source, raw_image, result_image, json_file, txt_file, object_count, objects_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["time"],
                data["source"],
                data["raw_image"],
                data["result_image"],
                data["json_file"],
                data["txt_file"],
                len(data["objects"]),
                json.dumps(data["objects"], ensure_ascii=False),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_history(limit: int = 20) -> List[Dict[str, Any]]:
    """读取最近识别历史。"""
    limit = max(1, min(limit, 200))
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM detections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    history = []
    for row in rows:
        item = dict(row)
        item["objects"] = json.loads(item.pop("objects_json") or "[]")
        history.append(item)
    return history


def get_latest() -> Optional[Dict[str, Any]]:
    history = get_history(limit=1)
    return history[0] if history else None


# =============================
# YOLO模型加载
# =============================
def get_model():
    """懒加载 YOLO 模型，第一次检测时才加载，避免启动时直接报错。"""
    global _model

    if _model is not None:
        return _model

    if YOLO is None:
        raise RuntimeError(
            "ultralytics 导入失败，请先安装依赖：pip install ultralytics。"
            f"原始错误：{YOLO_IMPORT_ERROR}"
        )

    model_path = BASE_DIR / CONFIG["model"]["path"]
    fallback_model = CONFIG["model"].get("fallback_model", "yolov8n.pt")

    if model_path.exists():
        selected_model = str(model_path)
    else:

        selected_model = fallback_model
        print(f"[WARN] 未找到 {model_path}，将使用 {fallback_model}。")

    with _model_lock:
        if _model is None:
            print(f"[INFO] 正在加载 YOLO 模型：{selected_model}")
            _model = YOLO(selected_model)
            print("[INFO] YOLO 模型加载完成")

    return _model


# =============================
# 摄像头/图片读取
# =============================
def capture_from_camera() -> Tuple[Path, str]:
    """从USB摄像头拍摄一张图片并保存。"""
    camera_cfg = CONFIG["camera"]
    camera_index = int(camera_cfg.get("index", 0))

    # Linux/香橙派下优先使用 V4L2，Windows/macOS 下使用默认方式。
    if platform.system().lower() == "linux":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(
            f"摄像头打开失败。请检查：1）USB摄像头是否插好；2）/dev/video* 是否存在；3）config.json 的 camera.index 是否正确。当前 index={camera_index}"
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(camera_cfg.get("width", 640)))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(camera_cfg.get("height", 480)))

    frame = None
    warmup_frames = int(camera_cfg.get("warmup_frames", 5))
    for _ in range(max(1, warmup_frames)):
        ok, frame = cap.read()
        time.sleep(0.03)

    cap.release()

    if frame is None or not ok:
        raise RuntimeError("摄像头读取失败：没有拿到图像帧。")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"camera_{timestamp}.jpg"
    path = RAW_DIR / filename
    cv2.imwrite(str(path), frame)

    return path, filename


def save_uploaded_image(file_storage) -> Tuple[Path, str]:
    """保存网页上传的图片，方便在没有摄像头时测试YOLO功能。"""
    if not file_storage or not file_storage.filename:
        raise RuntimeError("没有收到上传图片。")

    original = secure_filename(file_storage.filename)
    ext = Path(original).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        raise RuntimeError("只支持 jpg/jpeg/png/bmp/webp 图片。")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"upload_{timestamp}{ext}"
    upload_path = RAW_DIR / filename
    file_storage.save(str(upload_path))
    return upload_path, filename


# =============================
# 检测结果保存
# =============================
def xyxy_to_yolo_normalized(xyxy: List[float], image_width: int, image_height: int) -> Tuple[float, float, float, float]:
    """把 x1,y1,x2,y2 转换为 YOLO txt 常用的归一化中心点格式。"""
    x1, y1, x2, y2 = xyxy
    cx = ((x1 + x2) / 2) / image_width
    cy = ((y1 + y2) / 2) / image_height
    w = (x2 - x1) / image_width
    h = (y2 - y1) / image_height
    return cx, cy, w, h


def run_yolo_detection(image_path: Path, raw_filename: str, source: str) -> Dict[str, Any]:
    """
    对图片运行 YOLO 检测，并保存：
    1. 带框结果图 results/images/*.jpg
    2. 结构化结果 results/json/*.json
    3. YOLO风格文本结果 results/txt/*.txt
    4. SQLite历史记录 results/detections.db
    """
    model = get_model()
    model_cfg = CONFIG["model"]

    conf = float(model_cfg.get("confidence", 0.35))
    imgsz = int(model_cfg.get("imgsz", 640))
    device = model_cfg.get("device", "cpu")

    results = model.predict(
        source=str(image_path),
        conf=conf,
        imgsz=imgsz,
        device=device,
        save=False,
        verbose=False,
    )

    result = results[0]
    names = result.names
    image_height, image_width = result.orig_shape

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    stem = f"result_{timestamp}"
    result_image_filename = f"{stem}.jpg"
    json_filename = f"{stem}.json"
    txt_filename = f"{stem}.txt"

    objects: List[Dict[str, Any]] = []
    txt_lines: List[str] = []

    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            xyxy = [float(v) for v in box.xyxy[0].tolist()]
            class_name = str(names.get(cls_id, cls_id))
            cx, cy, w, h = xyxy_to_yolo_normalized(xyxy, image_width, image_height)

            objects.append(
                {
                    "class_id": cls_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "box_xyxy": {
                        "x1": round(xyxy[0], 2),
                        "y1": round(xyxy[1], 2),
                        "x2": round(xyxy[2], 2),
                        "y2": round(xyxy[3], 2),
                    },
                    "box_yolo_normalized": {
                        "cx": round(cx, 6),
                        "cy": round(cy, 6),
                        "w": round(w, 6),
                        "h": round(h, 6),
                    },
                }
            )

            txt_lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f} {confidence:.6f}")

    # 保存带检测框图片
    annotated = result.plot()
    result_image_path = RESULT_IMAGE_DIR / result_image_filename
    cv2.imwrite(str(result_image_path), annotated)

    # 保存 txt
    txt_path = TXT_DIR / txt_filename
    txt_path.write_text("\n".join(txt_lines), encoding="utf-8")

    # 保存 json
    data: Dict[str, Any] = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "raw_image": raw_filename,
        "result_image": result_image_filename,
        "json_file": json_filename,
        "txt_file": txt_filename,
        "image_size": {"width": image_width, "height": image_height},
        "confidence_threshold": conf,
        "objects": objects,
    }
    json_path = JSON_DIR / json_filename
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    record_id = save_detection_to_db(data)
    data["id"] = record_id

    # 检测完成后尝试硬件联动
    hardware_events = notify_hardware_if_needed(data)
    data["hardware_events"] = hardware_events

    return data


# =============================
# 硬件联动：灯、门禁、蜂鸣器等
# =============================
def notify_hardware_if_needed(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根据识别结果触发硬件控制。
    当前默认做法：当检测到 config.json 中 trigger_rules 配置的类别时，
    向硬件组提供的 HTTP 接口发送请求。

    """
    hardware_cfg = CONFIG.get("hardware", {})
    if not hardware_cfg.get("enabled", False):
        return []

    try:
        import requests
    except Exception as exc:
        return [{"status": "error", "message": f"requests 未安装，无法通知硬件：{exc}"}]

    events: List[Dict[str, Any]] = []
    objects = data.get("objects", [])
    timeout = float(hardware_cfg.get("timeout_seconds", 2))

    for rule in hardware_cfg.get("trigger_rules", []):
        classes = set(str(c).lower() for c in rule.get("classes", []))
        min_conf = float(rule.get("min_confidence", 0.0))

        matched = []
        for obj in objects:
            class_name = str(obj.get("class_name", "")).lower()
            confidence = float(obj.get("confidence", 0))
            if class_name in classes and confidence >= min_conf:
                matched.append(obj)

        if not matched:
            continue

        endpoint = rule.get("endpoint")
        method = str(rule.get("method", "POST")).upper()
        payload = dict(rule.get("payload", {}))
        payload.update(
            {
                "trigger_rule": rule.get("name", "unnamed_rule"),
                "detected_objects": matched,
                "detection_id": data.get("id"),
                "time": data.get("time"),
            }
        )

        if not endpoint:
            events.append({"status": "skipped", "message": "规则没有配置 endpoint", "rule": rule.get("name")})
            continue

        try:
            if method == "POST":
                resp = requests.post(endpoint, json=payload, timeout=timeout)
            else:
                resp = requests.get(endpoint, params=payload, timeout=timeout)

            events.append(
                {
                    "status": "sent",
                    "rule": rule.get("name"),
                    "endpoint": endpoint,
                    "http_status": resp.status_code,
                    "response": resp.text[:200],
                }
            )
        except Exception as exc:
            events.append({"status": "error", "rule": rule.get("name"), "endpoint": endpoint, "message": str(exc)})

    return events


# =============================
# Flask API / GUI
# =============================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/detect/camera", methods=["POST", "GET"])
def api_detect_camera():
    """从摄像头拍照并识别。GET/POST都支持，方便调试。"""
    try:
        image_path, raw_filename = capture_from_camera()
        data = run_yolo_detection(image_path, raw_filename, source="camera")
        return jsonify({"status": "ok", "data": data})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/detect/upload", methods=["POST"])
def api_detect_upload():
    """上传一张图片并识别。适合没有摄像头时调试，也适合后端传图片过来。"""
    try:
        file_storage = request.files.get("image")
        image_path, raw_filename = save_uploaded_image(file_storage)
        data = run_yolo_detection(image_path, raw_filename, source="upload")
        return jsonify({"status": "ok", "data": data})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/v1/vision/detect", methods=["POST"])
def api_v1_vision_detect():
    """
    B YOLO 对接小组后端/GUI 的兼容接口。

    小组统一接口：
    - 路径：POST /api/v1/vision/detect
    - 请求：multipart/form-data，可传 source=upload/camera 和 image 文件
    - 返回：label、confidence、bbox，并额外返回结果图片、json、txt 地址

    说明：
    - 当前压缩包内 weights/best.pt 是原有模型；
    - 训练完成三类模型后，直接覆盖 weights/best.pt 即可支持 light_bulb。
    """
    try:
        source = request.form.get("source", "upload")

        if source == "camera":
            image_path, raw_filename = capture_from_camera()
            data = run_yolo_detection(image_path, raw_filename, source="camera")
        else:
            file_storage = request.files.get("image")
            image_path, raw_filename = save_uploaded_image(file_storage)
            data = run_yolo_detection(image_path, raw_filename, source="upload")

        base_url = request.host_url.rstrip("/")

        detections = []
        for obj in data.get("objects", []):
            detections.append({
                "label": obj.get("class_name"),
                "class_id": obj.get("class_id"),
                "confidence": obj.get("confidence"),
                "bbox": obj.get("box_xyxy"),
                "bbox_yolo_normalized": obj.get("box_yolo_normalized")
            })

        light_bulb_detected = False
        for det in detections:
            label = str(det.get("label", "")).strip().lower()
            normalized_label = label.replace("-", "_").replace(" ", "_")
            if normalized_label in {"light_bulb", "bulb", "灯泡"}:
                light_bulb_detected = True
                break

        return jsonify({
            "status": "ok",
            "module": "yolo",
            "source": data.get("source"),
            "detection_id": data.get("id"),
            "created_at": data.get("time"),
            "model": {
                "name": "drone_fire_bulb_yolov8n",
                "classes": ["drone", "fire_extinguisher", "light_bulb"],
                "confidence_threshold": data.get("confidence_threshold")
            },
            "image": {
                "raw_image": data.get("raw_image"),
                "result_image": data.get("result_image"),
                "json_file": data.get("json_file"),
                "txt_file": data.get("txt_file"),
                "raw_image_url": f"{base_url}/files/raw/{data.get('raw_image')}",
                "result_image_url": f"{base_url}/files/result/{data.get('result_image')}",
                "json_url": f"{base_url}/files/json/{data.get('json_file')}",
                "txt_url": f"{base_url}/files/txt/{data.get('txt_file')}"
            },
            "detections": detections,
            "object_count": len(detections),
            "light_bulb_detected": light_bulb_detected,
            "hardware_events": data.get("hardware_events", [])
        })

    except Exception as exc:
        return jsonify({
            "status": "error",
            "module": "yolo",
            "message": str(exc)
        }), 500


@app.route("/api/latest", methods=["GET"])
def api_latest():
    latest = get_latest()
    return jsonify({"status": "ok", "data": latest})


@app.route("/api/history", methods=["GET"])
def api_history():
    limit = int(request.args.get("limit", 20))
    return jsonify({"status": "ok", "data": get_history(limit=limit)})


@app.route("/api/config", methods=["GET"])
def api_config():
    """给前端查看当前配置。出于安全，不返回硬件endpoint细节。"""
    safe_config = dict(CONFIG)
    if "hardware" in safe_config:
        safe_config["hardware"] = {
            "enabled": CONFIG.get("hardware", {}).get("enabled", False),
            "trigger_rule_count": len(CONFIG.get("hardware", {}).get("trigger_rules", [])),
        }
    return jsonify({"status": "ok", "data": safe_config})


@app.route("/files/raw/<path:filename>")
def file_raw(filename: str):
    return send_from_directory(RAW_DIR, filename)


@app.route("/files/result/<path:filename>")
def file_result(filename: str):
    return send_from_directory(RESULT_IMAGE_DIR, filename)


@app.route("/files/json/<path:filename>")
def file_json(filename: str):
    return send_from_directory(JSON_DIR, filename)


@app.route("/files/txt/<path:filename>")
def file_txt(filename: str):
    return send_from_directory(TXT_DIR, filename)


@app.route("/health", methods=["GET"])
def health():
    """健康检查接口，方便后端或GUI判断服务是否启动。"""
    model_path = BASE_DIR / CONFIG["model"]["path"]
    return jsonify(
        {
            "status": "ok",
            "model_path_exists": model_path.exists(),
            "database": str(DB_PATH),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


if __name__ == "__main__":
    init_db()
    server_cfg = CONFIG["server"]
    print("=" * 60)
    print("智能家居 YOLO 识别服务启动")
    print(f"访问地址：http://<香橙派IP>:{server_cfg.get('port', 5000)}")
    print("健康检查：http://127.0.0.1:%s/health" % server_cfg.get("port", 5000))
    print("=" * 60)
    app.run(
        host=server_cfg.get("host", "0.0.0.0"),
        port=int(server_cfg.get("port", 5000)),
        debug=bool(server_cfg.get("debug", False)),
    )
