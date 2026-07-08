# 模型权重放这里

推荐把你们训练好的模型复制为：

```text
weights/best.pt
```

如果没有 `best.pt`，程序会尝试使用 `yolov8n.pt`。首次使用 `yolov8n.pt` 时可能需要联网自动下载，所以比赛/验收前请提前准备好模型文件。

自定义类别名要和训练时 `data.yaml` 的 `names` 保持一致。例如：

```yaml
names: ['person', 'car', 'bulb']
```

如果想实现“检测到灯泡后开灯”，`config.json` 里的 `hardware.trigger_rules.classes` 要包含你的灯泡类别名，例如 `bulb` 或 `灯泡`。
