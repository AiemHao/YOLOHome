import paho.mqtt.publish as publish
import json
import time

# Cấu hình MQTT Broker
MQTT_HOST = "localhost"
MQTT_PORT = 1883

def send_telemetry(temp, humi, light):
    print(f"Đang gửi dữ liệu giả lập cảm biến: Temp={temp}, Humi={humi}, Light={light}")
    
    # Gửi tuần tự để Backend nhận đủ snapshot cảm biến
    publish.single("home/livingroom/sensor/temp", json.dumps({"value": temp}), hostname=MQTT_HOST, port=MQTT_PORT)
    time.sleep(0.1)
    publish.single("home/livingroom/sensor/humi", json.dumps({"value": humi}), hostname=MQTT_HOST, port=MQTT_PORT)
    time.sleep(0.1)
    publish.single("home/livingroom/sensor/light", json.dumps({"value": light}), hostname=MQTT_HOST, port=MQTT_PORT)
    
    print("✓ Đã gửi thành công! Hãy kiểm tra màn hình UI.")

if __name__ == "__main__":
    # Thay đổi các giá trị ở đây để test các trường hợp vượt ngưỡng khác nhau
    # Ví dụ: Nhiệt độ 35 độ C (vượt ngưỡng 30 độ C)
    send_telemetry(temp=35, humi=60, light=200)
