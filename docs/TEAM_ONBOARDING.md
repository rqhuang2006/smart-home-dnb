# Team Onboarding

这份文档给刚加入 GitHub 仓库的组员使用，目标是让大家能快速找到自己的任务、启动后端、理解协作方式。

## 1. 加入仓库后先做什么

1. 接受 GitHub 邀请。
2. 打开仓库：<https://github.com/rqhuang2006/smart-home-dnb>
3. 克隆项目：

```bash
git clone https://github.com/rqhuang2006/smart-home-dnb.git
cd smart-home-dnb
```

4. 阅读根目录 `README.md` 和 `智能家居后端API接口文档_C负责人.md`。
5. 如果要联调后端，进入 `backend/` 按 `backend/README.md` 启动。

## 2. 分支建议

不要直接在 `main` 上改。建议按任务建分支：

```bash
git checkout -b feature/gui
git checkout -b feature/face-recognition
git checkout -b feature/yolo-detection
git checkout -b feature/database-iot
git checkout -b feature/backend-api
```

改完后提交并推送：

```bash
git add .
git commit -m "describe your change"
git push -u origin <branch-name>
```

然后在 GitHub 上开 Pull Request。

## 3. 各角色入口

| 角色 | 先看什么 | 先做什么 |
|---|---|---|
| A 人脸识别 | `/api/v1/face/verify` 返回格式 | 用 2 真 1 假图片跑通 mock/真实识别结果 |
| B YOLO | `/api/v1/vision/detect` 返回格式 | 输出 label、confidence、bbox，与后端 JSON 对齐 |
| C 后端 API | `backend/app/main.py` | 保持接口稳定，补充真实数据库/算法/硬件适配 |
| D 数据库设备数据 | `/api/v1/iot/telemetry` 和 `/api/v1/sensors/history` | 设计表结构，模拟温度、灯光、门窗数据 |
| E GUI 集成 | `/api/v1/devices/status` 和 `/api/v1/dashboard/summary` | 做首页状态、历史查询、远程控制按钮 |

## 4. 邀请组员

如果已经知道组员 GitHub 用户名，可以由仓库管理员执行：

```bash
gh api -X PUT repos/rqhuang2006/smart-home-dnb/collaborators/<github-username> -f permission=push
```

也可以在网页操作：

1. 打开仓库 Settings。
2. 进入 Collaborators。
3. 点击 Add people。
4. 输入 GitHub 用户名或邮箱并发送邀请。

建议给普通组员 `Write` 权限即可。

## 5. 联调约定

- 接口路径尽量不要随意改；必须改时同步更新接口文档。
- mock 接口先保证 GUI 能开发，真实硬件/算法后续替换实现。
- 每个人提交前先说明改动影响了哪些接口或页面。
- 如果发现接口字段不够用，先在 issue 或群里说清楚字段名称、类型、用途。
