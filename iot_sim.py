# -*- coding: utf-8 -*-
import pymysql
import random
import time
from datetime import datetime

# ============数据库配置：端口3307、密码zty50427 ============
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "zty50427",
    "database": "iot_smart_system",
    "charset": "utf8mb4"
}
# ============================================================

def get_db_connection():
    """获取数据库连接，失败会打印报错信息"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"数据库连接失败！检查MySQL服务是否开启、端口/账号密码是否正确：{e}")
        return None

def generate_device_data():
    """生成温度、灯光、门窗的仿真数据"""
    now = datetime.now()
    hour = now.hour
    data_list = []

    # 1. 温度模拟：常规18-28℃，5%概率出现异常高温/低温
    if random.random() < 0.05:
        temp_val = round(random.choice([8.5, 35.2]), 1)
    else:
        temp_val = round(random.uniform(18, 28), 1)
    data_list.append({"dev_id": "temp_001", "val": temp_val})

    # 2. 灯光模拟：白天8:00-18:00亮度低(0-30)，夜晚亮度高(60-100)
    if 8 <= hour <= 18:
        light_val = random.randint(0, 30)
    else:
        light_val = random.randint(60, 100)
    data_list.append({"dev_id": "light_001", "val": light_val})

    # 3. 入户门模拟：10%概率开门，默认关闭
    door_val = 1 if random.random() < 0.1 else 0
    data_list.append({"dev_id": "door_001", "val": door_val})

    # 4. 窗户模拟：5%概率开窗
    win_val = 1 if random.random() < 0.05 else 0
    data_list.append({"dev_id": "win_001", "val": win_val})

    return data_list, now

def save_data_to_db():
    """把生成的数据同时写入实时表和历史表"""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    dev_data, now_time = generate_device_data()

    try:
        for item in dev_data:
            did = item["dev_id"]
            val = item["val"]
            # 更新实时表，已有数据就覆盖最新值
            sql_realtime = """
            INSERT INTO device_realtime(device_id, sensor_value, update_time)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE sensor_value=%s, update_time=%s
            """
            cursor.execute(sql_realtime, (did, val, now_time, val, now_time))
            # 插入历史表永久留存
            sql_history = """
            INSERT INTO device_history(device_id, sensor_value, report_time)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql_history, (did, val, now_time))
        conn.commit()
        print(f"✅ {now_time.strftime('%Y-%m-%d %H:%M:%S')} 数据写入成功")
        for d in dev_data:
            print(f"设备{d['dev_id']} 最新数值：{d['val']}")
        print("-"*40)
    except Exception as e:
        conn.rollback()
        print(f"❌ 数据写入出错：{e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=== 物联网设备数据模拟器已启动，每30秒自动上报一次数据 ===")
    while True:
        save_data_to_db()
        time.sleep(30) # 30秒生成一轮数据