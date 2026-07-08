# Run Locally

本地查看最推荐先跑 C 后端，再用 Swagger 或 GUI 页面访问。

## 1. C 后端 API

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

查看：

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/api/v1/health
```

## 2. IoT 模拟数据

另开一个终端，在项目根目录运行：

```bash
python iot_sim.py
```

默认会每 30 秒调用：

```text
POST http://127.0.0.1:8000/api/v1/iot/telemetry
```

如果要改间隔：

```powershell
$env:IOT_SIM_INTERVAL_SECONDS="5"
python iot_sim.py
```

## 3. 人脸识别模块

另开终端：

```bash
cd "Facial Recognition"
python -m pip install -r requirements.txt
python database/init_db.py
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

查看页面：

```text
http://127.0.0.1:8001/face/register
http://127.0.0.1:8001/face/verify
http://127.0.0.1:8001/face/logs
```

## 4. GUI 原型

确保 C 后端正在 `8000` 端口运行，然后直接用浏览器打开：

```text
web/smart-home-dnb-dashboard.html
web/nexus-iot-analytics.html
```

页面默认调用：

```text
http://127.0.0.1:8000/api/v1
```

如果浏览器显示离线/mock 数据，先检查：

- C 后端是否启动。
- `http://127.0.0.1:8000/api/v1/health` 是否能打开。
- 浏览器是否拦截本地文件访问；必要时可以在项目根目录启动一个静态服务：

```bash
python -m http.server 8080
```

然后访问：

```text
http://127.0.0.1:8080/web/smart-home-dnb-dashboard.html
```

## 5. YOLO 识别模块

```bash
cd smart_home_yolo_pack
python -m pip install -r requirements.txt
python app.py
```

查看：

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/health
```

说明：

- 仓库只保留 YOLO 源码、配置、页面和脚本。
- `weights/best.pt`、上传图片、识别结果、SQLite 结果库不提交到 Git。
- 如果没有 `weights/best.pt`，程序会尝试使用 `yolov8n.pt`，首次下载可能需要联网。
- 小组兼容接口是 `POST http://127.0.0.1:5000/api/v1/vision/detect`。
