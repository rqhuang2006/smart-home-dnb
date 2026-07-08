# -*- coding: utf-8 -*-
"""IoT device data simulator for the Smart Home DnB project.

Default mode sends generated telemetry to the C backend API:

    POST /api/v1/iot/telemetry

If D wants to test direct MySQL writes, set IOT_SIM_TARGET=db and configure
the IOT_DB_* environment variables. Do not hard-code real passwords here.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any


TARGET = os.getenv("IOT_SIM_TARGET", "api").strip().lower()
API_URL = os.getenv("IOT_API_URL", "http://127.0.0.1:8000/api/v1/iot/telemetry")
INTERVAL_SECONDS = int(os.getenv("IOT_SIM_INTERVAL_SECONDS", "30"))

DB_CONFIG = {
    "host": os.getenv("IOT_DB_HOST", "localhost"),
    "port": int(os.getenv("IOT_DB_PORT", "3307")),
    "user": os.getenv("IOT_DB_USER", "root"),
    "password": os.getenv("IOT_DB_PASSWORD", ""),
    "database": os.getenv("IOT_DB_NAME", "iot_smart_system"),
    "charset": "utf8mb4",
}


def generate_device_data() -> dict[str, Any]:
    """Generate one mock smart-home telemetry record."""
    hour = datetime.now().hour

    if random.random() < 0.05:
        temperature = round(random.choice([8.5, 35.2]), 1)
    else:
        temperature = round(random.uniform(18, 28), 1)

    if 8 <= hour <= 18:
        light_brightness = random.randint(0, 30)
    else:
        light_brightness = random.randint(60, 100)

    return {
        "temperature": temperature,
        "light_brightness": light_brightness,
        "door_open": random.random() < 0.10,
        "window_open": random.random() < 0.05,
        "fan_on": temperature >= 30,
    }


def send_to_api(payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        response_body = response.read().decode("utf-8")
    print(f"[api] {datetime.now():%Y-%m-%d %H:%M:%S} -> {response_body}")


def get_db_connection():
    try:
        import pymysql
    except ImportError as exc:
        raise RuntimeError("pymysql is required when IOT_SIM_TARGET=db") from exc

    if not DB_CONFIG["password"]:
        raise RuntimeError("IOT_DB_PASSWORD is required when IOT_SIM_TARGET=db")

    return pymysql.connect(**DB_CONFIG)


def send_to_db(payload: dict[str, Any]) -> None:
    device_values = {
        "temp_001": payload["temperature"],
        "light_001": payload["light_brightness"],
        "door_001": 1 if payload["door_open"] else 0,
        "win_001": 1 if payload["window_open"] else 0,
    }
    now_time = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for device_id, value in device_values.items():
            cursor.execute(
                """
                INSERT INTO device_realtime(device_id, sensor_value, update_time)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE sensor_value=%s, update_time=%s
                """,
                (device_id, value, now_time, value, now_time),
            )
            cursor.execute(
                """
                INSERT INTO device_history(device_id, sensor_value, report_time)
                VALUES (%s, %s, %s)
                """,
                (device_id, value, now_time),
            )
        conn.commit()
        print(f"[db] {now_time:%Y-%m-%d %H:%M:%S} saved {device_values}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def publish_once() -> None:
    payload = generate_device_data()
    if TARGET == "api":
        send_to_api(payload)
    elif TARGET == "db":
        send_to_db(payload)
    else:
        raise ValueError("IOT_SIM_TARGET must be api or db")


def main() -> None:
    print(f"IoT simulator started: target={TARGET}, interval={INTERVAL_SECONDS}s")
    print("Press Ctrl+C to stop.")
    while True:
        try:
            publish_once()
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"[api] failed to send telemetry: {exc}")
        except Exception as exc:
            print(f"[error] {exc}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
