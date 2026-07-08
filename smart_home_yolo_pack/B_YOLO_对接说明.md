# B YOLO 目标检测模块对接说明

## 1. 当前包说明

这个压缩包是 B 负责人 YOLO 模块的“小组对接版”。

已经加入小组兼容接口：

```http
POST /api/v1/vision/detect
```

已包含你原有模型：

```text
weights/best.pt
```

并额外备份一份：

```text
weights/best_drone_fire.pt
```

注意：当前压缩包里的 `best.pt` 仍是你原有的无人机 + 灭火器模型。等三类训练完成后，把新的三类模型覆盖到 `weights/best.pt` 即可。

---

## 2. 计划支持类别

三类模型训练完成后支持：

| class_id | label | 中文 |
|---|---|---|
| 0 | drone | 无人机 |
| 1 | fire_extinguisher | 灭火器 |
| 2 | light_bulb | 灯泡 |

---

## 3. 启动方式

```powershell
cd smart_home_yolo_pack
.\.venv\Scripts\activate
python app.py
```

如果没有 `.venv`，先安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --timeout 120
```

服务默认地址：

```text
http://127.0.0.1:5000
```

---

## 4. 小组兼容接口

### 上传图片识别

```powershell
curl.exe -X POST http://127.0.0.1:5000/api/v1/vision/detect -F "source=upload" -F "image=@C:\Users\34668\Desktop\test.jpg"
```

### 摄像头拍照识别

```powershell
curl.exe -X POST http://127.0.0.1:5000/api/v1/vision/detect -F "source=camera"
```

---

## 5. 返回格式示例

```json
{
  "status": "ok",
  "module": "yolo",
  "source": "upload",
  "model": {
    "name": "drone_fire_bulb_yolov8n",
    "classes": ["drone", "fire_extinguisher", "light_bulb"],
    "confidence_threshold": 0.35
  },
  "detections": [
    {
      "label": "light_bulb",
      "class_id": 2,
      "confidence": 0.86,
      "bbox": {
        "x1": 120.4,
        "y1": 80.2,
        "x2": 260.8,
        "y2": 410.5
      },
      "bbox_yolo_normalized": {
        "cx": 0.5,
        "cy": 0.5,
        "w": 0.2,
        "h": 0.3
      }
    }
  ],
  "object_count": 1,
  "light_bulb_detected": true
}
```

---

## 6. 和小组字段对齐

| 小组字段 | 本模块字段 |
|---|---|
| label | detections[i].label |
| confidence | detections[i].confidence |
| bbox | detections[i].bbox |

---

## 7. 保存位置

```text
images/          原始图片
results/images/  带框结果图
results/json/    JSON 检测结果
results/txt/     TXT 检测结果
```

---

## 8. 灯泡联动说明

`config.json` 中已预留灯泡触发规则：

```json
"classes": ["light_bulb"]
```

当前保持：

```json
"enabled": false
```

等训练出的三类模型确认能识别 `light_bulb` 后，再把它改成：

```json
"enabled": true
```

默认灯光控制接口预留为：

```http
POST http://127.0.0.1:8000/api/v1/devices/light/control
```
