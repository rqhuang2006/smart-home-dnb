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

GUI 分支目前还没有合入 main。想查看时：

```bash
git switch GUI
```

然后直接用浏览器打开：

```text
web/smart-home-dnb-dashboard.html
```

查看完回到主分支：

```bash
git switch main
```

## 5. YOLO 分支

YOLO 分支目前包含运行结果和模型大文件，暂时不建议直接合入 main。查看代码：

```bash
git switch yolo
```

查看完回到主分支：

```bash
git switch main
```

后续需要先清理运行产物，再按统一接口格式合并。
