# YOLO 模型预训练效果初步评估

评估时间：2026-07-08
模型文件：`smart_home_backend/models/yolo/best.pt`
样例图片目录：`incoming_modules/yolo_module/smart-home-dnb-yolo/smart_home_yolo_pack/images`

## 1. 模型实际类别

通过 `ultralytics.YOLO(best.pt).names` 读取到的类别为：

```text
0: drone
1: fire_extinguisher
2: light_bulb
```

注意：当前权重不是纯“两类模型”，而是三类模型，包含 `light_bulb`。如果本次验收只需要“无人机”和“灭火器”，应在说明中明确忽略 `light_bulb`，或后续换成真正的两类权重。

## 2. 是否能计算严格准确率

当前 `incoming_modules/yolo_module` 中没有发现标准测试集标注文件，例如：

- `data.yaml`
- `labels/*.txt`
- `valid/labels/*.txt`
- `test/labels/*.txt`

因此目前不能计算严格意义上的 mAP、Precision、Recall、F1。已有的 `results/txt` 和 `results/json` 是模型预测结果，不是人工真值标注，不能当作准确率依据。

## 3. 样例图片批量推理结果

使用阈值 `conf=0.35`、`imgsz=640`、CPU，对 11 张样例图片重新推理，结果如下：

| 图片 | 检测结果 |
|---|---|
| upload_20260708_184533_807.webp | 无检测 |
| upload_20260708_184555_690.webp | light_bulb 0.4454 |
| upload_20260708_184605_943.webp | 无检测 |
| upload_20260708_184610_263.webp | 无检测 |
| upload_20260708_184616_812.webp | fire_extinguisher 0.6579；fire_extinguisher 0.5766；drone 0.4657 |
| upload_20260708_185950_271.webp | light_bulb 0.4454 |
| upload_20260708_190014_077.webp | 无检测 |
| upload_20260708_190016_324.webp | 无检测 |
| upload_20260708_190016_828.webp | 无检测 |
| upload_20260708_190017_021.webp | 无检测 |
| upload_20260708_190028_789.webp | light_bulb 0.4454 |

统计：

- 11 张图片中，4 张有检测结果。
- `fire_extinguisher`：2 个检测框。
- `drone`：1 个检测框。
- `light_bulb`：3 个检测框。
- 只看本次需要的两类：灭火器 2 个框，无人机 1 个框，均出现在同一张样例图 `upload_20260708_184616_812.webp`。

## 4. 阈值敏感性

| 置信度阈值 | 有检测图片数 | 类别计数 |
|---|---:|---|
| 0.35 | 4 / 11 | light_bulb: 3, fire_extinguisher: 2, drone: 1 |
| 0.25 | 11 / 11 | fire_extinguisher: 5, light_bulb: 7, drone: 1 |
| 0.10 | 11 / 11 | fire_extinguisher: 8, light_bulb: 7, drone: 5 |

结论：

- `0.35` 比较保守，误检风险较低，但会漏掉一些低置信度目标。
- `0.25` 会显著增加检测数量，但也可能引入误检。
- `0.10` 太低，不建议作为验收阈值，低置信度无人机框明显增多。

## 5. 初步评价

在现有样例图片上，模型确实具备识别 `fire_extinguisher` 和 `drone` 的能力，但可用样例太少，尤其是无人机/灭火器有效样例不足，无法证明整体准确率。

当前更准确的说法是：

> 该权重可以在样例图中识别出灭火器和无人机，但当前仓库没有带人工标注的测试集，因此不能给出严格测试准确率。基于 11 张样例的 smoke test，在 conf=0.35 下检测到 fire_extinguisher 2 个框、drone 1 个框。

## 6. 建议验收方式

如果需要真正评估准确率，请准备一个标准 YOLO 测试集：

```text
dataset/
  images/test/*.jpg
  labels/test/*.txt
  data.yaml
```

`data.yaml` 示例：

```yaml
path: D:/project/dataset
train: images/train
val: images/test
test: images/test
names:
  0: drone
  1: fire_extinguisher
```

然后运行：

```powershell
python -c "from ultralytics import YOLO; model=YOLO('smart_home_backend/models/yolo/best.pt'); model.val(data='D:/project/dataset/data.yaml', split='test', conf=0.35, imgsz=640)"
```

这样才能得到 mAP50、mAP50-95、Precision、Recall 等正式指标。
