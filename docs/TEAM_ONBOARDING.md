# Team Onboarding

这份文档给刚加入仓库的组员使用。

## 1. 加入后先做什么

1. 接受 GitHub 仓库邀请。
2. 打开仓库：<https://github.com/rqhuang2006/smart-home-dnb>
3. 克隆项目：

```bash
git clone https://github.com/rqhuang2006/smart-home-dnb.git
cd smart-home-dnb
```

4. 阅读 `README.md`、`docs/RUN_LOCAL.md` 和接口文档。
5. 不要直接在 `main` 上改代码，先建自己的功能分支。

## 2. 分支建议

```bash
git checkout -b feature/gui
git checkout -b feature/face-recognition
git checkout -b feature/yolo-detection
git checkout -b feature/database-iot
git checkout -b feature/backend-api
```

提交并推送：

```bash
git add .
git commit -m "describe your change"
git push -u origin <branch-name>
```

然后在 GitHub 上开 Pull Request。

## 3. 角色入口

| 角色 | 先看什么 | 先做什么 |
|---|---|---|
| A 人脸识别 | `Facial Recognition/README.md` | 录入 2 真 1 假样例，确认 `/api/v1/face/verify` 返回格式 |
| B YOLO | C 接口文档里的 `/api/v1/vision/detect` | 对齐 `label/confidence/bbox`，不要提交运行结果和大模型到 Git |
| C 后端 API | `backend/app/main.py` | 保持统一接口稳定，负责聚合 A/B/D/E |
| D 数据库设备数据 | `database/schema_iot_smart_system.sql` 和 `iot_sim.py` | 用模拟数据调用 `/api/v1/iot/telemetry` |
| E GUI 集成 | `/api/v1/dashboard/summary` | 做首页状态、历史查询、远程控制按钮 |

## 4. 提交前自查

- 是否修改了接口路径或字段？如果是，同步更新文档。
- 是否提交了 `.env`、密码、数据库运行文件、`__pycache__`、结果图片？
- 是否能本地启动或至少说明依赖环境？
- 是否影响其他组员端口？默认端口：C 后端 8000、人脸 8001、YOLO 5000。
