# Smart Home YOLO Module

这是 B 负责人目标检测模块的源码目录。主分支只保留可维护源码、配置和页面，不提交模型权重、上传图片、识别结果或运行数据库。

## 启动

```bash
cd smart_home_yolo_pack
python -m pip install -r requirements.txt
python app.py
```

默认地址：

```text
http://127.0.0.1:5000/
```

健康检查：

```text
http://127.0.0.1:5000/health
```

## 模型文件

把最终训练好的模型放到：

```text
smart_home_yolo_pack/weights/best.pt
```

`*.pt` 文件已被 `.gitignore` 忽略。需要共享大模型时，建议使用 GitHub Release、网盘或 Git LFS。

## 小组兼容接口

上传图片识别：

```http
POST /api/v1/vision/detect
Content-Type: multipart/form-data
```

字段：

```text
source=upload
image=<file>
```

摄像头识别：

```http
POST /api/v1/vision/detect
Content-Type: multipart/form-data
```

字段：

```text
source=camera
```

返回格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "record_id": 1,
    "objects": [
      {
        "label": "light_bulb",
        "confidence": 0.86,
        "bbox": {
          "x1": 120.4,
          "y1": 80.2,
          "x2": 260.8,
          "y2": 410.5
        }
      }
    ],
    "light_bulb_detected": true
  }
}
```

识别记录：

```http
GET /api/v1/vision/records
```
