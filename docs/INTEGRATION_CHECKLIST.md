# Integration Checklist

这份清单用于阶段 1 和阶段 2 联调，帮助小组确认每个模块是否已经达到可集成状态。

## C 后端 API 当前可交付

- [x] GitHub 公开仓库已创建。
- [x] FastAPI mock 后端已搭建。
- [x] Swagger 文档可通过 `/docs` 查看。
- [x] 健康检查接口：`GET /api/v1/health`
- [x] 当前设备状态：`GET /api/v1/devices/status`
- [x] 历史数据查询：`GET /api/v1/sensors/history`
- [x] 设备数据上报：`POST /api/v1/iot/telemetry`
- [x] 人脸比对 mock：`POST /api/v1/face/verify`
- [x] YOLO 检测 mock：`POST /api/v1/vision/detect`
- [x] 灯光控制 mock：`POST /api/v1/devices/light/control`
- [x] 风扇控制 mock：`POST /api/v1/devices/fan/control`
- [x] 门禁控制 mock：`POST /api/v1/devices/door/control`
- [x] GUI 首页聚合：`GET /api/v1/dashboard/summary`

## A 人脸识别对接

- [ ] 确定人脸识别输入：图片路径、上传文件、摄像头帧。
- [ ] 确定 2 真 1 假测试样例。
- [ ] 输出字段与 `/api/v1/face/verify` 对齐：`matched`、`person_id`、`name`、`confidence`、`door_allowed`、`reason`。
- [ ] 确定通过阈值，例如 `confidence >= 0.75`。
- [ ] 识别成功后能触发门禁控制。

## B YOLO 对接

- [ ] 确定 YOLO 输入图片来源：本地路径或上传文件。
- [ ] 输出字段与 `/api/v1/vision/detect` 对齐：`label`、`confidence`、`bbox`。
- [ ] 确定是否需要保存带框结果图。
- [ ] 确认是否包含 `light_bulb` 或类似类别，用于触发灯光控制。
- [ ] GUI 能展示识别结果和识别记录。

## D 数据库与设备数据对接

- [ ] 确定数据库：SQLite 或 MySQL。
- [ ] 设计人员、门禁记录、图片、YOLO 记录、传感器历史、设备命令表。
- [ ] 用脚本定时调用 `/api/v1/iot/telemetry` 上报模拟数据。
- [ ] 历史查询支持按时间范围筛选。
- [ ] 控制命令需要记录来源和执行结果。

## E GUI 集成对接

- [ ] 首页展示 `/api/v1/dashboard/summary`。
- [ ] 状态面板展示温度、灯光、风扇、门窗。
- [ ] 历史页面调用 `/api/v1/sensors/history`。
- [ ] 远程控制按钮调用灯光、风扇、门禁控制接口。
- [ ] 展示人脸门禁结果和 YOLO 检测结果。

## 硬件/香橙派待确认

- [ ] 香橙派 IP 地址和系统环境。
- [ ] 摄像头型号和图片保存路径。
- [ ] 舵机/电机/灯光/风扇 GPIO 控制方式。
- [ ] 真实设备离线或控制失败时的返回格式。
- [ ] 是否由后端直接控制 GPIO，还是调用硬件组独立脚本。
