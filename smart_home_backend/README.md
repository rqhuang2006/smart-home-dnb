# Smart Home Integrated Backend

统一 FastAPI 后端，接入当前 `incoming_modules` 中的数据库、人脸识别、YOLO 和 GUI 模块。

## 模块入口检查

- 数据库模块：`incoming_modules/database_module/smart-home-dnb-DB/iot_sim.py`
  - 原模块使用 MySQL 表：`device_realtime`、`device_history`、`control_log`、`face_auth_user`、`ai_recording`。
  - 已在 `database/db.py` 适配为统一 SQLite：`data/smart_home.db`。
- 人脸模块：`incoming_modules/face_module/Facial Recognition/app.py`
  - 原模块已有 FastAPI。
  - 已复用其 `FaceEncoder`、`NoFaceFoundError`、`compare_embeddings` 核心逻辑。
- YOLO 模块：`incoming_modules/yolo_module/smart-home-dnb-yolo/smart_home_yolo_pack/app.py`
  - 原模块为 Flask。
  - 已按原 YOLO 推理流程封装到 `services/yolo_service.py`，模型懒加载缓存。
- GUI 模块：`incoming_modules/gui_module/smart-home-dnb-GUI/web/smart-home-dnb-dashboard.html`
  - 新 GUI 放在 `frontend/index.html`，只调用 `/api/v1` 新接口。

## 启动

```powershell
cd D:\project\smart_home_backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

开发阶段基础地址：`http://127.0.0.1:8000/api/v1`

GUI：`http://127.0.0.1:8000/`

## 已接入接口

- `POST /api/v1/persons`
- `GET /api/v1/persons?authorized=true`
- `POST /api/v1/face/verify`
- `POST /api/v1/devices/door/control`
- `POST /api/v1/images`
- `POST /api/v1/vision/detect`
- `GET /api/v1/vision/records`
- `POST /api/v1/iot/telemetry`
- `GET /api/v1/devices/status`
- `GET /api/v1/sensors/history`
- `POST /api/v1/devices/light/control`
- `POST /api/v1/devices/fan/control`
- `GET /api/v1/dashboard/summary`

## 完整测试顺序

1. 启动服务：`uvicorn main:app --host 0.0.0.0 --port 8000`
2. 健康检查：`GET http://127.0.0.1:8000/api/v1/health`
3. 上报 telemetry：`POST /api/v1/iot/telemetry`
4. 查看状态：`GET /api/v1/devices/status`
5. 控制灯光/风扇/门：`POST /api/v1/devices/light/control`、`fan/control`、`door/control`
6. 注册两名授权人员和一名未授权人员：`POST /api/v1/persons`
7. 查询授权人员：`GET /api/v1/persons?authorized=true`
8. 上传人脸验证图片：`POST /api/v1/face/verify`
9. 上传摄像头图片：`POST /api/v1/images`
10. YOLO 检测：`POST /api/v1/vision/detect`
11. 查看 YOLO 记录：`GET /api/v1/vision/records`
12. 查看传感器历史：`GET /api/v1/sensors/history?type=all`
13. 查看 Dashboard：`GET /api/v1/dashboard/summary`

## 适配说明

- 数据库模块原表名与接口文档不同，已在 `database/db.py` 做适配，路由层不直接写 SQL。
- 人脸验证不会直接控制硬件，只写 `access_logs` 并返回 `door_allowed`。
- 门、灯、风扇控制阶段一为 mock，都会写入 `device_commands` 并更新 `device_status`。
- 如果检测到 `light_bulb`，YOLO 服务返回 `trigger_action`，并调用 mock 灯光控制。

## 端口占用处理

如果提示 `WinError 10048`，说明 8000 端口已经被旧服务占用。可以先查占用进程：

```powershell
Get-NetTCPConnection -LocalPort 8000
```

也可以使用脚本启动，它会先检查端口：

```powershell
.\start_server.ps1
```
