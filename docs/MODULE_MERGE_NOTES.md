# Module Merge Notes

这份说明记录当前主分支对组员上传内容的合并取舍，方便后续继续联调。

## 已合入 main 的部分

| 模块 | 来源 | 合入内容 |
|---|---|---|
| A 人脸识别 | `main` 历史上传 | `Facial Recognition/` 源码、页面、测试图片 |
| C 后端 API | `main` | `backend/` FastAPI mock 服务与接口文档 |
| D 物联网数据 | `main` 历史上传 + 整理 | `iot_sim.py`、`.env.example`、`database/schema_iot_smart_system.sql` |
| E GUI | `origin/GUI` | `web/smart-home-dnb-dashboard.html`、`web/nexus-iot-analytics.html` |
| B YOLO | `origin/yolo` | `smart_home_yolo_pack/` 的源码、配置、静态页面、模板、脚本、`weights/README.md` |

## 本次没有合入的内容

| 内容 | 原因 | 后续处理 |
|---|---|---|
| `__pycache__/`、`*.pyc` | Python 运行缓存，不应提交 | 已由 `.gitignore` 忽略 |
| `127_0_0_1.sql` | 包含 phpMyAdmin/测试库等非项目内容 | 已整理为 `database/schema_iot_smart_system.sql` |
| YOLO `images/` | 上传图片/运行输入，不属于源码 | 本地运行时自动生成 |
| YOLO `results/` | 检测结果、SQLite 运行库，不属于源码 | 本地运行时自动生成 |
| YOLO `weights/best.pt` | 模型权重大，不适合直接进 Git | 放本机、GitHub Release、网盘或 Git LFS |

## 对接口做过的对齐

- C 后端新增/调整：
  - `POST /api/v1/images`
  - `GET /api/v1/vision/records`
  - `GET /api/v1/sensors/history` 返回数组，方便 GUI 直接渲染
  - 本地开发允许 CORS，方便 HTML 页面调用后端
  - mock 模式下温度达到 30.0°C 自动开启风扇
- YOLO 兼容接口调整：
  - `POST /api/v1/vision/detect` 返回 `code/message/data`
  - `GET /api/v1/vision/records` 返回 `code/message/data`
  - 检测对象统一为 `objects`，单项包含 `label`、`confidence`、`bbox`

## 后续还需要确认

- A 人脸模块是否由 C 后端转发，还是演示时独立运行 `8001`。
- B YOLO 最终模型文件如何分发，是否使用 GitHub Release 或网盘。
- D 数据库最终使用 SQLite 还是 MySQL。
- 硬件控制由 C 后端直接 GPIO，还是调用硬件组提供的脚本/服务。
