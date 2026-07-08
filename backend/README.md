# Smart Home Backend Mock API

这是智能家居项目 C 负责人用的 FastAPI 后端骨架。当前版本是 mock 模式，不依赖真实硬件、数据库、人脸识别模型或 YOLO 模型，方便 GUI、算法组和数据库组先并行联调。

## 1. 启动方式

进入后端目录：

```bash
cd backend
```

安装依赖：

```bash
python -m pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

本机访问：

```text
http://127.0.0.1:8000/api/v1/health
```

Swagger 接口文档：

```text
http://127.0.0.1:8000/docs
```

如果部署到香橙派，把 `127.0.0.1` 换成香橙派 IP，例如：

```text
http://<orange-pi-ip>:8000/docs
```

## 2. 已实现 mock 接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/health` | 后端健康检查 |
| GET | `/api/v1/devices/status` | 查询当前温度、灯光、风扇、门窗状态 |
| GET | `/api/v1/sensors/history` | 查询传感器历史数据 |
| POST | `/api/v1/iot/telemetry` | mock 设备数据上报 |
| POST | `/api/v1/images` | mock 图片记录 |
| POST | `/api/v1/face/verify` | mock 人脸比对和门禁判断 |
| POST | `/api/v1/vision/detect` | mock YOLO 目标检测 |
| GET | `/api/v1/vision/records` | 查询 YOLO 识别记录 |
| POST | `/api/v1/devices/light/control` | mock 灯光远程控制 |
| POST | `/api/v1/devices/fan/control` | mock 风扇远程控制 |
| POST | `/api/v1/devices/door/control` | mock 门禁远程控制 |
| GET | `/api/v1/dashboard/summary` | GUI 首页聚合数据 |

## 3. 快速测试示例

健康检查：

```bash
curl http://127.0.0.1:8000/api/v1/health
```

人脸识别，授权人员：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/face/verify \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"张三\"}"
```

人脸识别，未授权人员：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/face/verify \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"王五\"}"
```

控制灯光：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/light/control \
  -H "Content-Type: application/json" \
  -d "{\"on\":true,\"brightness\":80,\"source\":\"gui\"}"
```

控制风扇：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/fan/control \
  -H "Content-Type: application/json" \
  -d "{\"on\":true,\"source\":\"gui\",\"temperature\":30.2}"
```

上报设备数据：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/iot/telemetry \
  -H "Content-Type: application/json" \
  -d "{\"temperature\":28.6,\"light_brightness\":60,\"door_open\":false,\"window_open\":true,\"fan_on\":false}"
```

控制门禁：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices/door/control \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"open\",\"reason\":\"manual demo\",\"duration_seconds\":3}"
```

GUI 首页聚合数据：

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary
```

查询 YOLO 记录：

```bash
curl http://127.0.0.1:8000/api/v1/vision/records
```

## 4. 后续替换真实模块的位置

当前 mock 逻辑全部在 `app/main.py` 中：

| 当前 mock 位置 | 后续对接对象 |
|---|---|
| `authorized_people` | A 人脸识别负责人提供的人员库/特征库 |
| `verify_face()` | A 的人脸比对函数或服务 |
| `detect_objects()` | B 的 YOLO 检测函数或服务 |
| `device_status` / `sensor_history` | D 的数据库表和设备数据 |
| `control_light()` / `control_fan()` | GUI 按钮、硬件控制程序、香橙派 GPIO |

## 5. 当前集成状态

- GUI 页面已合入 `web/`，默认调用 `http://127.0.0.1:8000/api/v1`。
- YOLO 源码已合入 `smart_home_yolo_pack/`，模型权重和运行结果不进 Git。
- 人脸模块仍可独立运行在 `8001`，后续可由 C 后端转发或在演示流程中并行启动。
