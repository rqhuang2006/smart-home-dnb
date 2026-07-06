# Smart Home DnB

智能家居 Design and Build 项目后端与接口文档。当前仓库主要覆盖 C 负责人（物联网1后端 API）的阶段任务：搭建 FastAPI 后端骨架，定义模块之间的数据接口，并提供 mock 接口方便 GUI、算法组和数据库组并行开发。

## 项目背景

本项目需要设计并搭建一个以安全和舒适为重点的智能家居系统原型，包含：

- 自动门禁：授权人员通过人脸识别后开门。
- 监控摄像头：拍照、本地保存，并提供给 YOLO 识别。
- 目标识别：识别人、灯泡等目标并保存识别记录。
- 温度监控：显示室内温度，温度过高时启动风扇。
- 门窗状态：显示门窗开闭状态。
- 灯光控制：显示并控制灯光亮度。
- GUI：展示状态、历史数据、识别结果，并提供远程控制按钮。

## 小组分工

| 角色 | 负责人方向 | 主要任务 |
|---|---|---|
| A | 智科1 | 人脸识别、授权人员录入、人脸比对、2 真 1 假测试、门禁判断 |
| B | 智科2 | YOLO 目标检测、图片识别、识别记录、检测结果可视化 |
| C | 物联网1 | Flask/FastAPI/Node 后端，模块之间的数据接口 |
| D | 物联网2 | 数据表设计，温度、灯光、门窗状态数据模拟与存储 |
| E | 物联网或智科 | GUI 页面展示、历史数据查询、远程控制按钮、统一演示流程 |

## 当前完成内容

- 已创建公开 GitHub 仓库：<https://github.com/rqhuang2006/smart-home-dnb>
- 完成 C 负责人接口文档。
- 搭建 FastAPI mock 后端骨架。
- 实现 10 个 mock 接口，暂不依赖真实硬件。
- 已用本地 HTTP 请求验证接口可用。

## 组员快速入口

- 新成员加入与分支协作：[docs/TEAM_ONBOARDING.md](docs/TEAM_ONBOARDING.md)
- 阶段联调清单：[docs/INTEGRATION_CHECKLIST.md](docs/INTEGRATION_CHECKLIST.md)
- 后端启动与测试：[backend/README.md](backend/README.md)
- C 负责人接口文档：[智能家居后端API接口文档_C负责人.md](智能家居后端API接口文档_C负责人.md)

## 仓库结构

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── README.md
│   └── requirements.txt
├── 智能家居后端API接口文档_C负责人.md
├── 智能家居后端API接口文档_黄睿琦.docx
├── DnB26_Introduction.pptx
├── DnB26题目-智能家居.docx
└── README.md
```

## 后端启动

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
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 Swagger 接口文档：

```text
http://127.0.0.1:8000/docs
```

部署到香橙派时，把 `127.0.0.1` 换成香橙派 IP。

## 已实现接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/health` | 后端健康检查 |
| GET | `/api/v1/devices/status` | 查询当前设备状态 |
| GET | `/api/v1/sensors/history` | 查询传感器历史数据 |
| POST | `/api/v1/iot/telemetry` | mock 设备数据上报 |
| POST | `/api/v1/face/verify` | mock 人脸比对与门禁判断 |
| POST | `/api/v1/vision/detect` | mock YOLO 目标检测 |
| POST | `/api/v1/devices/light/control` | mock 灯光远程控制 |
| POST | `/api/v1/devices/fan/control` | mock 风扇远程控制 |
| POST | `/api/v1/devices/door/control` | mock 门禁远程控制 |
| GET | `/api/v1/dashboard/summary` | GUI 首页聚合数据 |

## 联调说明

当前后端是 mock 模式：

- A 可以先按 `/api/v1/face/verify` 对接人脸识别返回格式。
- B 可以先按 `/api/v1/vision/detect` 对接 YOLO 检测返回格式。
- D 可以先按 `/api/v1/sensors/history` 和后续数据库表设计对齐字段。
- E 可以直接用 `/api/v1/devices/status`、控制接口和 Swagger 文档开发 GUI。

后续拿到硬件或算法模块后，只需要替换 `backend/app/main.py` 中的 mock 数据和函数实现，接口路径和 JSON 格式尽量保持不变。

## GitHub 协作建议

建议后续按功能分支协作：

- `main`：稳定版本。
- `feature/backend-api`：后端接口开发。
- `feature/gui`：GUI 页面。
- `feature/face-recognition`：人脸识别。
- `feature/yolo-detection`：YOLO 检测。
- `feature/database-iot`：数据库与设备数据。

每次合并前先确认接口文档是否需要同步更新。
