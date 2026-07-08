# Smart Home DnB

智能家居 Design and Build 项目仓库。当前仓库用于小组协作，包含 C 后端 API、A 人脸门禁模块、D 设备数据模拟、接口文档和阶段联调说明。

GitHub 仓库：

```text
https://github.com/rqhuang2006/smart-home-dnb
```

## 1. 当前模块

| 模块 | 路径 | 默认端口 | 说明 |
|---|---|---:|---|
| C 后端 API | `backend/` | 8000 | 小组统一 mock API，GUI 优先接这里 |
| A 人脸门禁 | `Facial Recognition/` | 8001 | 授权人员录入、人脸验证、门禁日志 |
| D 设备数据模拟 | `iot_sim.py` | 无 | 默认向 C 后端上报模拟传感器数据 |
| 数据库 schema | `database/schema_iot_smart_system.sql` | 无 | 只包含项目 MySQL 表结构 |
| 协作文档 | `docs/` | 无 | 组员加入、联调清单、运行说明 |

## 2. 推荐运行顺序

先启动 C 后端 API：

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

查看后端 Swagger：

```text
http://127.0.0.1:8000/docs
```

再启动 IoT 模拟数据上报：

```bash
python iot_sim.py
```

如果要单独演示人脸模块：

```bash
cd "Facial Recognition"
python -m pip install -r requirements.txt
python database/init_db.py
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

查看人脸录入页面：

```text
http://127.0.0.1:8001/face/register
```

## 3. C 后端已实现接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/health` | 后端健康检查 |
| GET | `/api/v1/devices/status` | 查询当前设备状态 |
| GET | `/api/v1/sensors/history` | 查询传感器历史数据 |
| POST | `/api/v1/iot/telemetry` | 设备数据上报 |
| POST | `/api/v1/face/verify` | mock 人脸比对与门禁判断 |
| POST | `/api/v1/vision/detect` | mock YOLO 目标检测 |
| POST | `/api/v1/devices/light/control` | 灯光远程控制 |
| POST | `/api/v1/devices/fan/control` | 风扇远程控制 |
| POST | `/api/v1/devices/door/control` | 门禁远程控制 |
| GET | `/api/v1/dashboard/summary` | GUI 首页聚合数据 |

## 4. 重要协作约定

- `main` 保持可运行，组员改功能请开分支和 Pull Request。
- GUI 默认对接 C 后端：`http://127.0.0.1:8000/api/v1`。
- 人脸模块和 YOLO 模块可以先独立跑，后面由 C 后端统一聚合。
- 不要提交 `.env`、数据库运行文件、`__pycache__`、上传图片、识别结果图片、模型大文件。
- MySQL 密码只放本机环境变量或 `.env`，不要写进代码。

## 5. 更多文档

- 组员加入与协作：[docs/TEAM_ONBOARDING.md](docs/TEAM_ONBOARDING.md)
- 本地运行说明：[docs/RUN_LOCAL.md](docs/RUN_LOCAL.md)
- 阶段联调清单：[docs/INTEGRATION_CHECKLIST.md](docs/INTEGRATION_CHECKLIST.md)
- C 负责人接口文档：[智能家居后端API接口文档_C负责人.md](智能家居后端API接口文档_C负责人.md)
