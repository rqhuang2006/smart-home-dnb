# 智能家居 YOLO 识别负责人代码包

本代码包用于完成你的负责内容：

```text
图片读取 / 摄像头拍照
        ↓
YOLOv8 目标检测
        ↓
保存识别结果
        ↓
Web 页面展示
        ↓
可选：检测到指定物体后通知硬件组，例如检测到灯泡后开灯
```

适用设备：香橙派、Linux 开发板、普通电脑。  
推荐做法：电脑训练模型，香橙派部署运行。

---

## 1. 文件结构

```text
smart_home_yolo_pack/
├── app.py                         # 主程序：Flask + YOLO + 摄像头 + 保存 + 展示 + 硬件联动
├── config.json                    # 配置文件：模型路径、摄像头编号、置信度、硬件接口
├── requirements.txt               # Python依赖
├── install_orangepi.sh            # 香橙派/Linux一键安装脚本
├── run.sh                         # 启动脚本
├── README_使用说明.md             # 本说明
├── 接口文档_给其他组对接.md        # 给GUI/后端/硬件组看的接口说明
├── templates/
│   └── index.html                 # Web页面
├── static/
│   ├── app.js                     # 页面交互逻辑
│   └── style.css                  # 页面样式
├── weights/
│   └── README.md                  # 模型权重说明，best.pt 放这里
├── images/                        # 原始图片保存目录
└── results/
    ├── images/                    # 带检测框的结果图
    ├── json/                      # JSON识别结果
    ├── txt/                       # YOLO格式txt识别结果
    └── detections.db              # 自动生成，SQLite识别历史数据库
```

---

## 2. 在香橙派上安装

把整个文件夹复制到香橙派，例如放在：

```bash
/home/orangepi/smart_home_yolo_pack
```

进入目录：

```bash
cd /home/orangepi/smart_home_yolo_pack
```

运行安装脚本：

```bash
chmod +x install_orangepi.sh run.sh
./install_orangepi.sh
```

安装完成后，会生成虚拟环境：

```text
yolo_env/
```

---

## 3. 放置YOLO模型

把训练好的模型复制到：

```text
weights/best.pt
```

也就是：

```bash
cp 你的best.pt /home/orangepi/smart_home_yolo_pack/weights/best.pt
```

如果你还没有训练自己的模型，程序会尝试使用 `yolov8n.pt`。但是首次使用 `yolov8n.pt` 可能需要联网下载，所以比赛前最好提前准备好 `weights/best.pt`。

### 自定义模型类别名要求

如果你要实现“检测到灯泡后开灯”，训练时 `data.yaml` 里的类别名建议写成下面之一：

```yaml
names: ['bulb']
```

或者：

```yaml
names: ['light_bulb']
```

或者中文：

```yaml
names: ['灯泡']
```

如果你用的是别的名字，例如 `lamp`，需要同步修改 `config.json` 中的：

```json
"classes": ["bulb", "light_bulb", "灯泡"]
```

改成：

```json
"classes": ["lamp"]
```

---

## 4. 摄像头检查

插上USB摄像头后，查看设备：

```bash
ls /dev/video*
```

如果看到：

```text
/dev/video0
```

说明摄像头通常是 `index = 0`。

如果是 `/dev/video1`，则修改 `config.json`：

```json
"camera": {
  "index": 1,
  "width": 640,
  "height": 480,
  "warmup_frames": 5
}
```

---

## 5. 启动系统

在项目目录下运行：

```bash
./run.sh
```

看到类似信息：

```text
智能家居 YOLO 识别服务启动
访问地址：http://<香橙派IP>:5000
```

查看香橙派IP：

```bash
hostname -I
```

假设IP是 `192.168.1.88`，在电脑或手机浏览器访问：

```text
http://192.168.1.88:5000
```

---

## 6. 页面怎么用

打开网页后，你会看到两个主要功能：

### 功能1：摄像头拍照并识别

点击：

```text
摄像头拍照并识别
```

程序会自动完成：

```text
打开摄像头 → 拍照 → 保存原图 → YOLO检测 → 保存结果图 → 保存JSON/TXT → 页面显示
```

### 功能2：上传图片测试

如果摄像头暂时没有接好，可以选择一张图片，点击：

```text
上传并识别
```

这样可以先测试YOLO模型和网页展示功能。

---

## 7. 结果保存在哪里

每次识别会保存四类结果。

### 1）原始图片

```text
images/
```

示例：

```text
images/camera_20260706_165501_123.jpg
```

### 2）带检测框的结果图

```text
results/images/
```

示例：

```text
results/images/result_20260706_165502_456.jpg
```

### 3）JSON结构化结果

```text
results/json/
```

示例内容：

```json
{
  "time": "2026-07-06 16:55:02",
  "source": "camera",
  "raw_image": "camera_20260706_165501_123.jpg",
  "result_image": "result_20260706_165502_456.jpg",
  "objects": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.89,
      "box_xyxy": {
        "x1": 100.1,
        "y1": 80.2,
        "x2": 300.4,
        "y2": 420.7
      }
    }
  ]
}
```

### 4）TXT检测结果

```text
results/txt/
```

格式：

```text
类别ID 中心x 中心y 宽 高 置信度
```

注意：这是检测结果TXT，和训练标注TXT类似，但多保存了置信度，方便统计和展示。

### 5）SQLite历史数据库

```text
results/detections.db
```

网页“识别历史”表格就是从这里读取。

---

## 8. 与硬件组对接：检测到灯泡后开灯

默认硬件联动是关闭的。配置在 `config.json`：

```json
"hardware": {
  "enabled": false,
  "timeout_seconds": 2,
  "trigger_rules": [
    {
      "name": "检测到灯泡后开灯",
      "classes": ["bulb", "light_bulb", "灯泡"],
      "min_confidence": 0.4,
      "method": "POST",
      "endpoint": "http://127.0.0.1:5001/light/on",
      "payload": {
        "device": "light",
        "action": "on"
      }
    }
  ]
}
```

如果硬件组给了你HTTP接口，例如：

```text
http://192.168.1.90:5001/light/on
```

你就改成：

```json
"enabled": true,
"endpoint": "http://192.168.1.90:5001/light/on"
```

当YOLO检测到 `bulb`、`light_bulb` 或 `灯泡`，并且置信度大于 `0.4` 时，程序会自动向这个接口发送POST请求。

### 如果硬件组不用HTTP，而是让你直接控制GPIO

打开 `app.py`，找到：

```python
notify_hardware_if_needed(data)
```

里面已经写了注释。你可以把HTTP请求换成GPIO控制代码。

例如伪代码：

```python
import OPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)
GPIO.output(7, GPIO.HIGH)
```

具体引脚号要问硬件组，不能自己随便写。

---

## 9. 与GUI组/后端组对接

你的程序已经提供了HTTP接口，其他组可以直接调用。

常用接口：

```text
GET  /health                  检查服务是否启动
POST /api/detect/camera       摄像头拍照并识别
POST /api/detect/upload       上传图片并识别
GET  /api/latest              获取最新识别结果
GET  /api/history?limit=20    获取识别历史
```

详细看：

```text
接口文档_给其他组对接.md
```

---

## 10. 常见问题

### 问题1：摄像头打不开

先执行：

```bash
ls /dev/video*
```

如果只有 `/dev/video1`，就把 `config.json` 的 camera.index 改成 1。

如果没有任何 `/dev/video*`，说明系统没识别到摄像头，检查USB接口、电源、摄像头驱动。

### 问题2：运行很慢

香橙派CPU算力有限，建议：

```json
"imgsz": 416
```

或：

```json
"imgsz": 320
```

并且使用最轻量的模型，比如 `yolov8n.pt` 或你自己训练的轻量版 `best.pt`。

### 问题3：torch/ultralytics安装失败

这是香橙派ARM环境常见问题。解决方向：

1. 换用支持你系统架构的 PyTorch 安装包。
2. 在电脑训练并导出 ONNX/NCNN，然后在香橙派部署推理。
3. 第一版验收可以先在电脑跑通完整链路，再迁移到香橙派。

### 问题4：检测不到灯泡

检查三点：

1. 模型是否真的训练过灯泡类别。
2. `data.yaml` 中类别名和 `config.json` 中 `classes` 是否一致。
3. 置信度阈值是否太高，可以先把 `confidence` 改成 `0.25` 测试。

---

## 11. 你演示时可以这样说

> 我负责YOLO识别模块。我实现了从摄像头拍照或上传图片读取图像，然后使用YOLOv8模型进行目标检测。检测完成后，系统会保存原始图片、带检测框的结果图、JSON结构化识别结果和TXT格式检测结果，同时写入本地SQLite数据库。前端网页可以实时展示最新识别结果和历史记录。如果检测到指定物体，例如灯泡，程序可以通过HTTP接口或GPIO代码与硬件组对接，实现自动开灯等功能。


---

## 12. 可选：测试硬件联动模拟器

如果硬件组还没有给你真实接口，可以先开一个模拟硬件服务。

打开一个新终端：

```bash
cd /home/orangepi/smart_home_yolo_pack
source yolo_env/bin/activate
python hardware_mock_server.py
```

然后把 `config.json` 改成：

```json
"hardware": {
  "enabled": true
}
```

保持 endpoint 为：

```text
http://127.0.0.1:5001/light/on
```

当YOLO检测到灯泡类别时，模拟器终端会打印收到的开灯请求。
