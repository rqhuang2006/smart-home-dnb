# B YOLO 模块接口测试脚本
# 使用前：把一张测试图片放到 C:\Users\34668\Desktop\test.jpg

$baseUrl = "http://127.0.0.1:5000"
$testImage = "C:\Users\34668\Desktop\test.jpg"

Write-Host "1. 测试健康检查"
curl.exe "$baseUrl/health"

Write-Host "`n2. 测试小组兼容 YOLO 接口：POST /api/v1/vision/detect"
curl.exe -X POST "$baseUrl/api/v1/vision/detect" `
  -F "source=upload" `
  -F "image=@$testImage"

Write-Host "`n测试完成"
