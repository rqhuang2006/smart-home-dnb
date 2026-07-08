"""
硬件组接口模拟器
用途：在还没有和硬件组对接前，测试“检测到灯泡后开灯”的HTTP联动是否正常。

运行：
    source yolo_env/bin/activate
    python hardware_mock_server.py

然后把 config.json 中 hardware.enabled 改为 true，endpoint 保持：
    http://127.0.0.1:5001/light/on
"""

from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/light/on", methods=["POST", "GET"])
def light_on():
    data = request.get_json(silent=True) or request.args.to_dict()
    print("[硬件模拟器] 收到开灯请求：", data)
    return jsonify({"status": "ok", "message": "模拟开灯成功", "received": data})


@app.route("/light/off", methods=["POST", "GET"])
def light_off():
    data = request.get_json(silent=True) or request.args.to_dict()
    print("[硬件模拟器] 收到关灯请求：", data)
    return jsonify({"status": "ok", "message": "模拟关灯成功", "received": data})


if __name__ == "__main__":
    print("硬件模拟器启动：http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
