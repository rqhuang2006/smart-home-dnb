# 手动测试图片说明

目录：`smart_home_backend/data/images/camera`

本批图片来自 Wikimedia Commons 等公开可访问图片源，来源信息保存于：

- `smart_home_backend/data/yolo_eval/downloaded_test_images_sources.json`

当前 YOLO 模型在 `conf=0.35`、`imgsz=640` 下对这 10 张图片的预期类别命中情况保存于：

- `smart_home_backend/data/yolo_eval/downloaded_test_images_predictions.json`

## 灭火器测试图片

| 文件名 | 预期类别 | 当前模型检测情况 |
|---|---|---|
| fire_extinguisher_test_01.jpg | fire_extinguisher | 命中，confidence 0.9632 |
| fire_extinguisher_test_02.jpg | fire_extinguisher | 命中，confidence 0.9652 |
| fire_extinguisher_test_03.jpg | fire_extinguisher | 命中，confidence 0.9634 |
| fire_extinguisher_test_04.jpg | fire_extinguisher | 命中，confidence 0.9819 |
| fire_extinguisher_test_05.jpg | fire_extinguisher | 命中，confidence 0.7592 |

## 无人机测试图片

| 文件名 | 预期类别 | 当前模型检测情况 |
|---|---|---|
| drone_test_01.jpg | drone | 命中，confidence 0.8890 |
| drone_test_02.jpg | drone | 命中，confidence 0.7384 |
| drone_test_03.jpg | drone | 命中，最高 confidence 0.6639 |
| drone_test_04.jpg | drone | 命中，confidence 0.8140 |
| drone_test_05.jpg | drone | 命中，confidence 0.7119 |

## 手动测试方式

启动后端后，在 GUI 页面选择上述任意图片上传检测：

```text
http://127.0.0.1:8000/
```

也可以用命令行测试，例如：

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/vision/detect `
  -F "source=manual" `
  -F "image=@smart_home_backend/data/images/camera/fire_extinguisher_test_01.jpg"
```

或：

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/vision/detect `
  -F "source=manual" `
  -F "image=@smart_home_backend/data/images/camera/drone_test_01.jpg"
```
