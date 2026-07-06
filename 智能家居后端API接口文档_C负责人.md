# 智能家居系统后端 API 接口文档

版本：v0.1  
编写人：黄睿琦
适用阶段：阶段 1 独立组件开发、阶段 2 系统集成  

---

## 1. 项目目标与 C 负责人范围

本项目需要完成一个以安全和舒适为重点的智能家居系统原型，包含自动门禁、人脸识别、YOLO 目标识别、温度监控、门窗状态、灯光控制、GUI 展示与历史数据查询。

C 负责人主要负责后端 API 与模块之间的数据接口，具体包括：

1. 提供统一 HTTP API，供 GUI、识别算法、设备数据模块调用。
2. 定义 A/B/D/E 各模块之间的数据格式、接口路径、返回结构。
3. 负责后端服务框架选型、接口联调、错误码、演示流程接口。
4. 在香橙派上部署后端服务，或至少保证接口可迁移到香橙派运行。
5. 明确数据库读写边界：表结构和模拟数据由 D 主责，C 负责通过 API 调用数据库。

不属于 C 单独主责但需要对接的内容：

| 模块 | 主责人 | 与 C 的交叉点 | C 需要提供/确认 |
|---|---|---|---|
| A 人脸识别 | 智科1 | 授权人员录入、人脸比对、门禁判断 | 人员管理接口、人脸验证接口、门禁决策返回格式 |
| B YOLO 识别 | 智科2 | 图片识别、识别记录、检测结果可视化 | 图片上传/读取接口、检测结果写入接口、识别记录查询接口 |
| D 数据库与设备数据 | 物联网2 | 数据表设计、温度/灯光/门窗状态模拟与存储 | 数据库访问约定、传感器数据上报接口、历史查询接口 |
| E GUI 与集成 | 物联网或智科 | 页面展示、历史数据查询、远程控制按钮、统一演示流程 | 前端 API 文档、控制接口、状态查询接口、演示用聚合接口 |

---

## 2. 总体架构建议

### 2.1 物理与软件结构

建议以香橙派作为边缘网关：

```text
摄像头 / 传感器 / 执行器
        |
        v
香橙派 Orange Pi
  - FastAPI 后端服务
  - 本地图片保存目录
  - SQLite / MySQL 数据库连接
  - 调用人脸识别模块
  - 调用 YOLO 识别模块
        |
        v
GUI Web 页面 / 手机端页面
```

### 2.2 后端服务基础约定

基础地址：

```text
http://<orange-pi-ip>:8000/api/v1
```

开发阶段可使用：

```text
http://127.0.0.1:8000/api/v1
```

数据格式：

```text
Content-Type: application/json
图片上传使用 multipart/form-data
时间统一使用 ISO 8601，例如 2026-07-06T21:30:00+08:00
```

统一返回格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误返回格式：

```json
{
  "code": 4001,
  "message": "person not found",
  "data": null
}
```

常用错误码：

| code | 含义 |
|---:|---|
| 0 | 成功 |
| 4000 | 请求参数错误 |
| 4001 | 数据不存在 |
| 4002 | 识别失败 |
| 4003 | 未授权人员 |
| 5000 | 后端内部错误 |
| 5001 | 设备离线或控制失败 |

---

## 3. 数据对象定义

### 3.1 授权人员 Person

由 A 主责人负责人脸数据业务，D 负责人负责表结构落库，C 提供 API。

```json
{
  "person_id": 1,
  "name": "张三",
  "role": "student",
  "authorized": true,
  "face_image_path": "/data/images/faces/zhangsan.jpg",
  "created_at": "2026-07-06T21:30:00+08:00"
}
```

### 3.2 人脸比对结果 FaceVerifyResult

```json
{
  "matched": true,
  "person_id": 1,
  "name": "张三",
  "confidence": 0.92,
  "door_allowed": true,
  "reason": "authorized person"
}
```

### 3.3 YOLO 检测结果 DetectionResult

由 B 主责识别算法与可视化结果，C 提供记录写入和查询接口。

```json
{
  "record_id": 101,
  "image_path": "/data/images/camera/20260706_213000.jpg",
  "objects": [
    {
      "label": "person",
      "confidence": 0.87,
      "bbox": [120, 80, 260, 360]
    }
  ],
  "created_at": "2026-07-06T21:30:00+08:00"
}
```

### 3.4 设备状态 DeviceStatus

由 D 主责数据模拟与存储，E 通过 GUI 展示和控制，C 提供统一接口。

```json
{
  "temperature": 29.5,
  "fan_on": true,
  "light_on": true,
  "light_brightness": 80,
  "door_open": false,
  "window_open": true,
  "updated_at": "2026-07-06T21:30:00+08:00"
}
```

### 3.5 传感器记录 SensorRecord

```json
{
  "record_id": 501,
  "temperature": 29.5,
  "light_brightness": 80,
  "door_open": false,
  "window_open": true,
  "fan_on": true,
  "created_at": "2026-07-06T21:30:00+08:00"
}
```

---

## 4. C 主责 API 清单

### 4.1 健康检查

用于 GUI、联调和演示前检查后端是否在线。

```http
GET /api/v1/health
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "service": "smart-home-backend",
    "status": "running",
    "device": "Orange Pi",
    "time": "2026-07-06T21:30:00+08:00"
  }
}
```

主责：C  
调用方：E、全组联调

---

## 5. 人员与门禁接口（A 与 C 交叉）

### 5.1 新增授权人员

A 负责人用于录入授权人员。C 负责接收数据并保存。

```http
POST /api/v1/persons
Content-Type: multipart/form-data
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 人员姓名 |
| role | string | 否 | 身份，如 student/teacher |
| authorized | boolean | 是 | 是否授权开门 |
| face_image | file | 是 | 人脸图片 |

响应：

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

主责：C 提供接口，A 提供人脸录入逻辑，D 保存数据表。

### 5.2 查询授权人员列表

```http
GET /api/v1/persons?authorized=true
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "person_id": 1,
      "name": "张三",
      "role": "student",
      "authorized": true
    }
  ]
}
```

主责：C  
调用方：A、E

### 5.3 人脸比对与门禁判断

用于“2 真 1 假”测试。A 负责人做人脸比对算法，C 负责 API 封装与门禁判断结果返回。

```http
POST /api/v1/face/verify
Content-Type: multipart/form-data
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| face_image | file | 是 | 当前摄像头拍到的人脸图片 |

响应，真授权人员：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "matched": true,
    "person_id": 1,
    "name": "张三",
    "confidence": 0.92,
    "door_allowed": true,
    "reason": "authorized person"
  }
}
```

响应，假人员或未授权：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "matched": false,
    "person_id": null,
    "name": null,
    "confidence": 0.31,
    "door_allowed": false,
    "reason": "unknown or unauthorized person"
  }
}
```

主责：A 完成人脸识别，C 定义接口和门禁返回格式，E 展示结果。

### 5.4 门禁控制

用于控制门禁电机/舵机打开或关闭。硬件控制方式由电管/电子专业确认，C 只定义统一接口。

```http
POST /api/v1/devices/door/control
Content-Type: application/json
```

请求：

```json
{
  "action": "open",
  "reason": "face authorized",
  "duration_seconds": 3
}
```

响应：

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

主责：C 提供接口，硬件组提供实际开门控制，A/E 调用。

---

## 6. 图像与 YOLO 接口（B 与 C 交叉）

### 6.1 上传或保存摄像头图片

摄像头拍照后，本地保存并登记图片路径。香橙派上建议保存到 `/data/images/camera/`。

```http
POST /api/v1/images
Content-Type: multipart/form-data
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| image | file | 是 | 摄像头图片 |
| source | string | 否 | camera/manual |

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "image_id": 201,
    "image_path": "/data/images/camera/20260706_213000.jpg"
  }
}
```

主责：C  
调用方：B、E、硬件摄像头模块

### 6.2 调用 YOLO 目标检测

B 负责人实现 YOLO 模型，C 可以封装成统一 API。

```http
POST /api/v1/vision/detect
Content-Type: application/json
```

请求：

```json
{
  "image_id": 201,
  "image_path": "/data/images/camera/20260706_213000.jpg"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "record_id": 101,
    "objects": [
      {
        "label": "person",
        "confidence": 0.87,
        "bbox": [120, 80, 260, 360]
      },
      {
        "label": "light_bulb",
        "confidence": 0.76,
        "bbox": [300, 100, 380, 190]
      }
    ],
    "trigger_action": {
      "type": "light_on",
      "executed": true,
      "reason": "detected light_bulb"
    }
  }
}
```

说明：题目提到“通过摄像头检测到灯泡图片后，控制灯亮”，因此检测到 `light_bulb` 时可以触发灯光控制接口。

主责：B 实现检测，C 封装接口并记录结果，E 展示结果。

### 6.3 查询 YOLO 识别记录

```http
GET /api/v1/vision/records?start=2026-07-06T00:00:00+08:00&end=2026-07-06T23:59:59+08:00
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "record_id": 101,
      "image_path": "/data/images/camera/20260706_213000.jpg",
      "objects": [
        {
          "label": "person",
          "confidence": 0.87,
          "bbox": [120, 80, 260, 360]
        }
      ],
      "created_at": "2026-07-06T21:30:00+08:00"
    }
  ]
}
```

主责：C 提供查询接口，B 写入识别数据，E 做结果可视化。

---

## 7. 设备与传感器接口（D 与 C 交叉）

### 7.1 设备数据上报

D 负责人可用模拟数据或真实传感器数据调用该接口，把温度、门窗、灯光、风扇状态写入数据库。

```http
POST /api/v1/iot/telemetry
Content-Type: application/json
```

请求：

```json
{
  "temperature": 29.5,
  "light_brightness": 80,
  "door_open": false,
  "window_open": true,
  "fan_on": true
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "record_id": 501,
    "saved": true
  }
}
```

主责：D 产生和存储数据，C 提供接口。

### 7.2 获取当前设备状态

```http
GET /api/v1/devices/status
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "temperature": 29.5,
    "fan_on": true,
    "light_on": true,
    "light_brightness": 80,
    "door_open": false,
    "window_open": true,
    "updated_at": "2026-07-06T21:30:00+08:00"
  }
}
```

主责：C  
调用方：E

### 7.3 查询历史数据

GUI 需要在特定时间间隔内检索温度、灯光、门、窗状态。

```http
GET /api/v1/sensors/history?start=2026-07-06T00:00:00+08:00&end=2026-07-06T23:59:59+08:00&type=all
```

参数：

| 参数 | 必填 | 说明 |
|---|---|---|
| start | 是 | 开始时间 |
| end | 是 | 结束时间 |
| type | 否 | all/temperature/light/door/window |

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "record_id": 501,
      "temperature": 29.5,
      "light_brightness": 80,
      "door_open": false,
      "window_open": true,
      "fan_on": true,
      "created_at": "2026-07-06T21:30:00+08:00"
    }
  ]
}
```

主责：C 提供查询接口，D 提供数据表和数据源，E 展示图表。

---

## 8. 远程控制接口（E 与 C 交叉）

### 8.1 控制灯光

```http
POST /api/v1/devices/light/control
Content-Type: application/json
```

请求：

```json
{
  "on": true,
  "brightness": 80,
  "source": "gui"
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "light_on": true,
    "light_brightness": 80
  }
}
```

主责：C 提供接口，E 调用按钮，硬件组执行灯光控制，D 记录状态。

### 8.2 控制风扇/空调

温度过高时系统可自动启动风扇；GUI 也可以远程控制。

```http
POST /api/v1/devices/fan/control
Content-Type: application/json
```

请求：

```json
{
  "on": true,
  "source": "auto_temperature",
  "temperature": 30.2
}
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "fan_on": true
  }
}
```

主责：C 提供接口，E 可调用，D 记录状态，硬件组执行。

---

## 9. GUI 聚合接口（E 与 C 交叉）

为了方便 E 负责人快速做首页展示，C 可以提供一个聚合接口，减少前端同时调多个接口。

```http
GET /api/v1/dashboard/summary
```

响应：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "device_status": {
      "temperature": 29.5,
      "fan_on": true,
      "light_on": true,
      "light_brightness": 80,
      "door_open": false,
      "window_open": true
    },
    "latest_face_access": {
      "matched": true,
      "name": "张三",
      "door_allowed": true,
      "created_at": "2026-07-06T21:30:00+08:00"
    },
    "latest_detection": {
      "record_id": 101,
      "objects": ["person", "light_bulb"],
      "created_at": "2026-07-06T21:30:00+08:00"
    }
  }
}
```

主责：C  
调用方：E

---

## 10. 建议数据库表（与 D 对齐）

数据库设计由 D 主责，以下是 C 建议的最小可用表，便于 API 落地。

| 表名 | 用途 | 主要字段 | 对接模块 |
|---|---|---|---|
| persons | 授权人员 | id, name, role, authorized, face_image_path, created_at | A/C/D/E |
| access_logs | 门禁记录 | id, person_id, matched, confidence, door_allowed, reason, image_path, created_at | A/C/E |
| images | 图片记录 | id, image_path, source, created_at | B/C |
| detection_records | YOLO 记录 | id, image_id, result_json, created_at | B/C/E |
| sensor_records | 传感器历史 | id, temperature, light_brightness, door_open, window_open, fan_on, created_at | C/D/E |
| device_commands | 远程控制记录 | id, device_type, command_json, status, source, created_at | C/D/E/硬件组 |

开发阶段建议使用 SQLite，方便香橙派本地部署；如果后期多人联调需要远程访问，可切换 MySQL。

---

## 11. 演示流程接口顺序

### 11.1 人脸门禁演示：2 真 1 假

1. A 录入 2 个授权人员：
   - `POST /api/v1/persons`
2. 摄像头或本地图片提交人脸比对：
   - `POST /api/v1/face/verify`
3. 后端返回 `door_allowed=true/false`
4. 如果为真，调用门禁控制：
   - `POST /api/v1/devices/door/control`
5. GUI 查询并显示最新门禁结果：
   - `GET /api/v1/dashboard/summary`

### 11.2 YOLO 识别演示

1. 上传或保存摄像头图片：
   - `POST /api/v1/images`
2. 调用 YOLO 检测：
   - `POST /api/v1/vision/detect`
3. 查询识别记录：
   - `GET /api/v1/vision/records`
4. GUI 展示检测框、标签、置信度。
5. 如果检测到灯泡图片，可调用：
   - `POST /api/v1/devices/light/control`

### 11.3 温度、灯光、门窗历史查询演示

1. D 模块定时上报模拟或真实数据：
   - `POST /api/v1/iot/telemetry`
2. GUI 查询当前状态：
   - `GET /api/v1/devices/status`
3. GUI 查询历史曲线：
   - `GET /api/v1/sensors/history`
4. 温度超过阈值时，后端或硬件控制模块调用：
   - `POST /api/v1/devices/fan/control`

---

## 12. 香橙派部署约定

建议目录：

```text
/home/orangepi/smart-home/
  backend/
  data/
    images/
      camera/
      faces/
    smart_home.db
```

建议端口：

```text
后端 API：8000
GUI 页面：3000 或 8080
```

后端启动命令示例：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

香橙派上的硬件接口需要硬件组确认：

| 设备 | 可能方式 | 待确认内容 |
|---|---|---|
| 摄像头 | USB 摄像头 / CSI 摄像头 | 图片保存路径、拍照触发方式 |
| 门禁电机/舵机 | GPIO / PWM | 开门角度、持续时间、GPIO 引脚 |
| 风扇/空调模型 | GPIO / 继电器 / PWM | 温度阈值、开关方式 |
| 灯光 | GPIO / PWM | 是否支持亮度调节、亮度范围 |
| 门窗状态 | 磁簧开关 / 微动开关 / 模拟数据 | open/close 的电平定义 |
| 温度传感器 | DHT11/DHT22/DS18B20 或模拟数据 | 采样频率、异常值处理 |

---

## 13. 待其他负责人确认的问题

### A 人脸识别负责人需要确认

1. 人脸识别模块是否由后端直接调用 Python 函数，还是单独运行成服务。
2. 人脸图片是否需要保存原图，还是只保存特征向量。
3. `confidence` 阈值多少算通过。
4. 2 真 1 假测试人员名单和图片格式。

### B YOLO 负责人需要确认

1. YOLO 模型输出类别名称，例如是否包含 `light_bulb`。
2. 检测结果是否需要输出带框图片。
3. YOLO 是由后端同步调用，还是 B 提供单独检测脚本/服务。
4. 图片输入路径和检测结果 JSON 格式是否接受本文档定义。

### D 数据库与设备数据负责人需要确认

1. 最终使用 SQLite 还是 MySQL。
2. 传感器数据字段是否与本文档一致。
3. 模拟数据生成频率，例如每 2 秒或每 5 秒一条。
4. 设备控制命令是否需要单独记录到 `device_commands`。

### E GUI 与集成负责人需要确认

1. GUI 使用 Web 还是手机端。
2. 首页需要展示哪些字段。
3. 历史数据图表需要哪些筛选条件。
4. 远程控制按钮包括哪些：灯、风扇、门禁、其他设备。

### 硬件/电管/电子方向需要确认

1. 香橙派是否确定作为主控或后端部署设备。
2. 摄像头、舵机、风扇、灯光、门窗开关的实际接线方案。
3. 后端是否直接控制 GPIO，还是通过硬件控制程序转发。
4. 设备离线或执行失败时如何反馈。

---

## 14. C 负责人当天可交付清单

1. 本接口文档 v0.1。
2. 与 A/B/D/E 对齐接口路径和 JSON 字段。
3. 搭建 FastAPI 项目骨架。
4. 先实现以下 mock 接口，方便 GUI 和算法组并行开发：
   - `GET /api/v1/health`
   - `GET /api/v1/devices/status`
   - `GET /api/v1/sensors/history`
   - `POST /api/v1/face/verify`
   - `POST /api/v1/vision/detect`
   - `POST /api/v1/devices/light/control`
   - `POST /api/v1/devices/fan/control`

---

## 15. 最小联调优先级

第一优先级：

1. `GET /api/v1/health`
2. `GET /api/v1/devices/status`
3. `POST /api/v1/iot/telemetry`
4. `GET /api/v1/sensors/history`

第二优先级：

1. `POST /api/v1/persons`
2. `POST /api/v1/face/verify`
3. `POST /api/v1/devices/door/control`

第三优先级：

1. `POST /api/v1/images`
2. `POST /api/v1/vision/detect`
3. `GET /api/v1/vision/records`
4. `GET /api/v1/dashboard/summary`

这样安排可以保证 D 和 E 先联调数据展示，A/B 再逐步接入算法模块，最后完成统一演示流程。
