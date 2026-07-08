# Smart Home Face Access Backend

这是大学小学期 Design and Build 智能家居系统中的人脸识别门禁模块。

本模块负责：

- 授权人员录入
- 授权人员列表查询
- 人脸验证与门禁判断
- mock 门禁开门/关门
- 门禁识别日志
- Dashboard 最近一次人脸识别结果
- 阶段一“2 真 1 假”演示测试页面和测试图片

开发运行地址：

```text
http://127.0.0.1:8001
```

API 统一前缀：

```text
/api/v1
```

所有接口返回格式统一为：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误返回示例：

```json
{
  "code": 4001,
  "message": "person not found",
  "data": null
}
```

## 1. 克隆后如何运行

### 1.1 准备 Python

建议使用 Python 3.10 到 3.12。

先进入项目目录：

```bash
cd smart-home-face-access
```

如果你是在 Windows 上，可以在项目目录创建虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
```

如果你是在 macOS / Linux / 香橙派上：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 1.2 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括：

- FastAPI
- Uvicorn
- SQLite 标准库
- OpenCV
- NumPy
- Jinja2
- python-multipart
- requests

### 1.3 初始化数据库

```bash
python database/init_db.py
```

这会自动生成：

```text
database/smarthome.db
```

注意：这个数据库是运行时文件，不需要提交到 GitHub。

### 1.4 启动后端

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

启动成功后访问：

```text
http://127.0.0.1:8001
```

如果你是在香橙派或局域网机器上部署，其他设备可以访问：

```text
http://<orange-pi-ip>:8001
```

API 地址就是：

```text
http://127.0.0.1:8001/api/v1
```

## 2. 页面怎么用

项目自带了三个简单测试页面，方便不接正式 GUI 时单独演示。

### 2.1 人员录入页面

```text
http://127.0.0.1:8001/face/register
```

可以做这些事：

- 输入姓名 `name`
- 输入身份 `role`
- 选择是否授权 `authorized`
- 上传人脸图片 `face_image`
- 查看已录入人员
- 删除录入错的人员

### 2.2 人脸验证页面

```text
http://127.0.0.1:8001/face/verify
```

上传一张待验证的人脸图片，页面会显示：

- `matched`：是否匹配到授权人员
- `name`：匹配到的人名
- `confidence`：相似度，越高越像同一个人
- `door_allowed`：是否允许开门
- `reason`：判断原因

如果 `door_allowed=true`，页面会出现“调用门禁开门”按钮。点击后会调用 mock 门禁控制接口。

### 2.3 识别记录页面

```text
http://127.0.0.1:8001/face/logs
```

可以查看最近的人脸验证记录。每次调用 `/api/v1/face/verify` 都会写入一条日志，包括没有检测到人脸的情况。

## 3. 2 真 1 假演示流程

项目里已经准备好了测试图片：

```text
test/demo/authorized_zhangsan_register.jpg
test/demo/authorized_zhangsan_verify.jpg
test/demo/authorized_lisi_register.jpg
test/demo/authorized_lisi_verify.jpg
test/demo/unauthorized_verify.jpg
```

演示步骤：

1. 打开人员录入页面：

```text
http://127.0.0.1:8001/face/register
```

2. 录入第一个授权人员：

```text
name: 张三
role: student
authorized: true
face_image: test/demo/authorized_zhangsan_register.jpg
```

3. 录入第二个授权人员：

```text
name: 李四
role: student
authorized: true
face_image: test/demo/authorized_lisi_register.jpg
```

4. 打开人脸验证页面：

```text
http://127.0.0.1:8001/face/verify
```

5. 上传张三验证图：

```text
test/demo/authorized_zhangsan_verify.jpg
```

期望结果：

```text
matched=true
name=张三
door_allowed=true
reason=authorized person
```

6. 上传李四验证图：

```text
test/demo/authorized_lisi_verify.jpg
```

期望结果：

```text
matched=true
name=李四
door_allowed=true
reason=authorized person
```

7. 上传未授权人员验证图：

```text
test/demo/unauthorized_verify.jpg
```

期望结果：

```text
matched=false
name=null
door_allowed=false
reason=unknown or unauthorized person
```

8. 查看识别记录：

```text
http://127.0.0.1:8001/face/logs
```

确认三次识别都写入 `access_logs`。

## 4. 主要 API

### 4.1 授权人员录入

```text
POST /api/v1/persons
Content-Type: multipart/form-data
```

字段：

```text
name: string，必填
role: string，选填
authorized: boolean，必填
face_image: file，必填
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "person_id": 1,
    "name": "张三",
    "authorized": true
  }
}
```

### 4.2 查询人员列表

```text
GET /api/v1/persons
GET /api/v1/persons?authorized=true
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "person_id": 1,
      "name": "张三",
      "role": "student",
      "authorized": true,
      "created_at": "2026-07-07T12:00:00+08:00"
    }
  ]
}
```

### 4.3 删除人员

```text
DELETE /api/v1/persons/{person_id}
```

成功响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "person_id": 1,
    "name": "张三",
    "deleted": true
  }
}
```

人员不存在：

```json
{
  "code": 4001,
  "message": "person not found",
  "data": null
}
```

删除人员会删除该人员的人脸图片和特征文件。历史日志会保留，但对应 `person_id` 会置空。

### 4.4 人脸验证

```text
POST /api/v1/face/verify
Content-Type: multipart/form-data
```

字段：

```text
face_image: file，必填
```

授权人员识别成功：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "matched": true,
    "person_id": 1,
    "name": "张三",
    "confidence": 0.9899,
    "door_allowed": true,
    "reason": "authorized person"
  }
}
```

未授权人员：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "matched": false,
    "person_id": null,
    "name": null,
    "confidence": 0.8128,
    "door_allowed": false,
    "reason": "unknown or unauthorized person"
  }
}
```

没有检测到人脸：

```json
{
  "code": 4002,
  "message": "no face detected",
  "data": {
    "matched": false,
    "person_id": null,
    "name": null,
    "confidence": 0,
    "door_allowed": false,
    "reason": "no face detected"
  }
}
```

### 4.5 门禁控制

```text
POST /api/v1/devices/door/control
Content-Type: application/json
```

请求示例：

```json
{
  "action": "open",
  "reason": "face authorized",
  "duration_seconds": 3
}
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "door_open": true,
    "action": "open"
  }
}
```

注意：人脸验证接口只返回 `door_allowed`，不会直接控制硬件。真正开门需要再调用本接口。

### 4.6 门禁日志

```text
GET /api/v1/access/logs?limit=50
```

### 4.7 Dashboard 聚合接口

```text
GET /api/v1/dashboard/summary
```

响应示例：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "latest_face_access": {
      "matched": true,
      "name": "张三",
      "door_allowed": true,
      "created_at": "2026-07-07T12:00:00+08:00"
    }
  }
}
```

## 5. 人脸识别判断逻辑

项目默认使用 OpenCV 兜底方案：

1. 检测图片里是否有人脸。
2. 截取最大人脸区域。
3. 提取轻量特征向量。
4. 与数据库中 `authorized=true` 的人员特征逐个比较。
5. 找到距离最小的人。
6. 如果 `distance <= threshold`，认为匹配成功。

当前默认阈值：

```text
OPENCV_MATCH_THRESHOLD=0.05
```

`confidence` 是相似度，范围大致为 `0.0` 到 `1.0`，越高表示越像同一个人。内部判断主要看 `distance` 是否低于阈值。

如果后续安装 `face_recognition`，代码会自动优先使用它，并使用：

```text
FACE_MATCH_THRESHOLD=0.55
```

## 6. 项目结构

```text
smart-home-face-access/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── database/
│   ├── __init__.py
│   └── init_db.py
├── face_module/
│   ├── __init__.py
│   ├── api_response.py
│   ├── config.py
│   ├── door_control.py
│   ├── face_service.py
│   └── face_utils.py
├── routes/
│   ├── __init__.py
│   ├── door_routes.py
│   ├── face_routes.py
│   └── person_routes.py
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── access_logs.html
│   ├── face_register.html
│   └── face_verify.html
├── data/
│   ├── embeddings/.gitkeep
│   └── images/
│       ├── access/.gitkeep
│       ├── camera/.gitkeep
│       └── faces/.gitkeep
└── test/
    ├── README.md
    ├── demo/
    └── source/
```

## 7. 上传 GitHub 注意事项

建议上传：

```text
app.py
main.py
requirements.txt
README.md
.gitignore
database/
face_module/
routes/
static/
templates/
test/
data/ 里的 .gitkeep
```

不要上传：

```text
.venv/
__pycache__/
database/*.db
data/images/faces/*
data/images/access/*
data/images/camera/*
data/embeddings/*
*.log
storage/
.agents/
.codex/
```

原因：

- `.venv/` 是本机虚拟环境，体积大，换电脑后也不一定能用。
- `database/smarthome.db` 是运行时数据库，clone 后可以重新生成。
- `data/images/*` 和 `data/embeddings/*` 是运行中上传的人脸图片和特征文件，不应提交真实人员数据。
- `test/` 是公开演示素材，可以提交。

本项目已经配置 `.gitignore`，用 Git 命令提交时会自动忽略这些运行文件。

## 8. 后期接入真实硬件

当前默认是 mock 门禁：

```text
HARDWARE_MODE=mock
```

后续如果接 GPIO、PWM、串口或另一个硬件 HTTP 服务，不需要改外部 API，只需要改 `face_module/door_control.py` 里的 `control_door()`。

也可以使用 HTTP 方式转发给硬件服务：

```bash
HARDWARE_MODE=http
HARDWARE_DOOR_URL=http://127.0.0.1:9000/door/open
DOOR_OPEN_DURATION_SECONDS=3
```

外部仍然调用：

```text
POST /api/v1/devices/door/control
```
