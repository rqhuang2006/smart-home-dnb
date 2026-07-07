# 人脸识别测试图片

这个目录用于本项目阶段一演示“2 真 1 假”，也额外提供 5 张不同人的人脸图片做扩展测试。图片来自公开的 Wikimedia Commons 肖像页，已经整理成适合本项目上传测试的文件。

## 目录说明

```text
test/
├── demo/
│   ├── authorized_zhangsan_register.jpg
│   ├── authorized_zhangsan_verify.jpg
│   ├── authorized_lisi_register.jpg
│   ├── authorized_lisi_verify.jpg
│   ├── unauthorized_verify.jpg
│   ├── extra_person_01_kamala_harris.jpg
│   ├── extra_person_02_george_w_bush.jpg
│   ├── extra_person_03_bill_clinton.jpg
│   ├── extra_person_04_hillary_clinton.jpg
│   └── extra_person_05_michelle_obama.jpg
└── source/
    ├── obama_source.jpg
    ├── biden_source.jpg
    ├── trump_source.jpg
    ├── kamala_harris_source.jpg
    ├── george_w_bush_source.jpg
    ├── bill_clinton_source.jpg
    ├── hillary_clinton_source.jpg
    └── michelle_obama_source.jpg
```

## 2 真 1 假使用流程

1. 启动后端：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. 打开人员录入页面：

```text
http://127.0.0.1:8000/face/register
```

3. 录入第一个授权人员：

```text
name: 张三
role: student
authorized: true
face_image: test/demo/authorized_zhangsan_register.jpg
```

4. 录入第二个授权人员：

```text
name: 李四
role: student
authorized: true
face_image: test/demo/authorized_lisi_register.jpg
```

5. 打开人脸验证页面：

```text
http://127.0.0.1:8000/face/verify
```

6. 上传 `test/demo/authorized_zhangsan_verify.jpg`。

期望：

```text
matched=true
name=张三
door_allowed=true
reason=authorized person
```

7. 上传 `test/demo/authorized_lisi_verify.jpg`。

期望：

```text
matched=true
name=李四
door_allowed=true
reason=authorized person
```

8. 上传 `test/demo/unauthorized_verify.jpg`。

期望：

```text
matched=false
name=null
door_allowed=false
reason=unknown or unauthorized person
```

## 额外测试图片

除固定演示图外，还新增了 5 张不同人的测试图，可用于测试未授权识别、删除人员后再验证、或临时录入更多人员：

```text
test/demo/extra_person_01_kamala_harris.jpg
test/demo/extra_person_02_george_w_bush.jpg
test/demo/extra_person_03_bill_clinton.jpg
test/demo/extra_person_04_hillary_clinton.jpg
test/demo/extra_person_05_michelle_obama.jpg
```

这些图片已用当前项目的 `FaceEncoder` 验证过，每张最终测试图都能检测到 1 张人脸并提取特征。

## 当前算法验证结果

当前项目使用 OpenCV 兜底人脸特征方案时，默认阈值为：

```text
OPENCV_MATCH_THRESHOLD=0.05
```

固定演示图片在该阈值下的本地验证结果：

```text
张三 self distance=0.0101 matched=True
李四 self distance=0.0235 matched=True
未授权 vs 张三 distance=0.1872 matched=False
未授权 vs 李四 distance=0.1874 matched=False
张三 vs 李四 distance=0.0940 matched=False
```

说明：`distance` 越小越像同一个人，`confidence` 越高越像同一个人。接口返回的是 `confidence`，内部匹配判断使用 `distance <= threshold`。

## 图片来源

- Barack Obama official portrait: https://commons.wikimedia.org/wiki/File:President_Barack_Obama.jpg
- Joe Biden presidential portrait: https://commons.wikimedia.org/wiki/File:Joe_Biden_presidential_portrait.jpg
- Donald Trump official portrait: https://commons.wikimedia.org/wiki/File:Donald_Trump_official_portrait.jpg
- Kamala Harris Vice Presidential Portrait: https://commons.wikimedia.org/wiki/File:Kamala_Harris_Vice_Presidential_Portrait.jpg
- George W. Bush portrait: https://commons.wikimedia.org/wiki/File:George-W-Bush.jpeg
- Bill Clinton portrait: https://commons.wikimedia.org/wiki/File:Bill_Clinton.jpg
- Hillary Clinton official Secretary of State portrait crop: https://commons.wikimedia.org/wiki/File:Hillary_Clinton_official_Secretary_of_State_portrait_crop.jpg
- Michelle Obama 2013 official portrait: https://commons.wikimedia.org/wiki/File:Michelle_Obama_2013_official_portrait.jpg

这些图片只作为课程演示和本地功能测试素材。正式项目部署时，请使用实际授权人员本人同意采集的人脸图片。
