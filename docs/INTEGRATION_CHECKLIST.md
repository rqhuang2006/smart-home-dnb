# Integration Checklist

这份清单用于阶段 1 和阶段 2 联调。

## C 后端 API

- [x] GitHub 公开仓库已创建。
- [x] FastAPI mock 后端已搭建。
- [x] Swagger 文档可通过 `/docs` 查看。
- [x] `GET /api/v1/health`
- [x] `GET /api/v1/devices/status`
- [x] `GET /api/v1/sensors/history`
- [x] `POST /api/v1/iot/telemetry`
- [x] `POST /api/v1/face/verify`
- [x] `POST /api/v1/vision/detect`
- [x] `POST /api/v1/devices/light/control`
- [x] `POST /api/v1/devices/fan/control`
- [x] `POST /api/v1/devices/door/control`
- [x] `GET /api/v1/dashboard/summary`

## A 人脸识别

- [ ] 人脸服务默认端口改为 8001，避免和 C 后端 8000 冲突。
- [ ] 准备 2 个授权人员和 1 个未授权人员样例。
- [ ] 输出字段对齐：`matched`、`person_id`、`name`、`confidence`、`door_allowed`、`reason`。
- [ ] 明确阈值和失败原因。
- [ ] 后续决定：合入 C 后端，或由 C 后端转发到人脸服务。

## B YOLO

- [ ] `/api/v1/vision/detect` 返回格式需要和 C 后端统一：`code/message/data`。
- [ ] 检测列表字段统一为 `objects`，单项包含 `label`、`confidence`、`bbox`。
- [ ] 运行结果、上传图片、SQLite 数据库、模型权重不要直接提交到 Git。
- [ ] 如需保存大模型，使用 GitHub Release、网盘或 Git LFS。

## D 数据库与设备数据

- [x] 已提供干净 MySQL schema：`database/schema_iot_smart_system.sql`。
- [x] `iot_sim.py` 默认通过 C 后端 API 上报，不再写死数据库密码。
- [ ] 如果要直写 MySQL，复制 `.env.example` 为 `.env` 并配置 `IOT_DB_*`。
- [ ] 历史数据查询最终由数据库支持时间范围筛选。

## E GUI

- [ ] GUI 默认接口地址：`http://127.0.0.1:8000/api/v1`。
- [ ] 首页展示 `/api/v1/dashboard/summary`。
- [ ] 历史页面调用 `/api/v1/sensors/history`。
- [ ] 远程控制按钮调用灯光、风扇、门禁控制接口。
- [ ] 展示人脸识别结果和 YOLO 检测结果。

## 硬件/香橙派

- [ ] 确认香橙派 IP 地址和系统环境。
- [ ] 确认摄像头、舵机、风扇、灯光、门窗开关接线。
- [ ] 确认后端直接控制 GPIO，还是调用硬件组脚本/服务。
- [ ] 设备离线或控制失败时返回 `code=5001`。
