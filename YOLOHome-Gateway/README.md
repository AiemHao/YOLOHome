# YOLOHome Gateway

Gateway MQTT <-> Serial cho hệ YOLOHome.

## API docs
- Chi tiết API MQTT: [docs/mqtt-api.md](docs/mqtt-api.md)

## Mục tiêu
- Điều khiển thiết bị qua MQTT và chuyển lệnh xuống kit qua Serial.
- Nhận trạng thái định kỳ từ kit và publish lại MQTT.
- Quản lý danh sách thiết bị từ config.
- Chuẩn hóa MQTT payload theo JSON.

## Topic schema
Cấu trúc chung:

{prefix}/{location}/{device_type}/{property}/{action_or_status}

Giá trị đang dùng:
- prefix: home
- location: livingroom

Các nhóm topic:
- Sensor: home/livingroom/sensor/{type}
- Device command: home/livingroom/device/{type}/set
- Device state: home/livingroom/device/{type}/state
- System request: home/system/getall
- System response: home/system/stateall

## MQTT JSON Spec (bắt buộc)
Tất cả MQTT payload phải là JSON object.

### 1) Device command /set
Payload chuẩn cho device là:

```json
{
  "action": "..."
}
```

Ví dụ:
- LED on: {"action":"on"}
- LED off: {"action":"off"}
- Servo on: {"action":"on"}
- Servo off: {"action":"off"}

### 2) Sensor state publish
Gateway publish dạng:

```json
{
  "value": "25.5"
}
```

### 3) Device state publish
Gateway publish dạng:

```json
{
  "action": "on"
}
```

Ví dụ:
- LED đang bật: {"action":"on"}
- Fan đang tắt: {"action":"off"}
- Servo đang bật: {"action":"on"}

### 4) System stateall
Gateway publish snapshot:

```json
{
  "temp": "25.5",
  "humi": "60",
  "light": "700",
  "led": "1",
  "fan": "0",
  "servo": "1"
}
```

## Danh sách thiết bị quản lý từ config
Nguồn sự thật là managed_devices trong config.yml.

Ý nghĩa:
- Chỉ thiết bị trong managed_devices mới được nhận lệnh device/set.
- Controller dùng metadata này để xác định type, switch behavior, topic info.
- Serial mapping chỉ lưu tại `devices` (không lặp lại trong `managed_devices`).

Ví dụ cấu hình:

```yaml
managed_devices:
  temp:
    type: sensor
    unit: celsius
    is_switch: false
    description: Living room temperature
  led:
    type: device
    unit: binary
    is_switch: true
    description: Main LED relay
```

## API truy vấn thông tin thiết bị
MainController có các phương thức:
- managed_device_list(): trả về toàn bộ tên thiết bị đang quản lý.
- device_info(device_name): trả về metadata + state hiện tại + history + topics của thiết bị đó.
- all_devices_info(): trả về thông tin đầy đủ cho tất cả thiết bị, KHÔNG bao gồm `serial_abbr`.

## State cache và history
- Không lưu state ngay khi nhận command MQTT.
- Chỉ cập nhật state khi kit trả về qua Serial.
- Tách riêng:
  - sensor_state_history
  - device_state_history
- Mỗi thiết bị giữ tối đa app.state_history_size trạng thái gần nhất.

## Cấu hình mẫu

```yaml
mqtt:
  host: localhost
  port: 1883
  username: ''
  password: ''
  subscribe_topics:
    - home/livingroom/device/led/set
    - home/livingroom/device/fan/set
    - home/livingroom/device/servo/set
    - home/system/getall
  topics:
    prefix: "home"
    location: "livingroom"
    system_getall: "home/system/getall"
    system_state_all: "home/system/stateall"

serial:
  port: COM3
  baudrate: 115200
  timeout: 1

app:
  loop_interval: 0.1
  log_level: INFO
  state_history_size: 20

rate_limit:
  mqtt_to_serial: 0.1
  serial_to_mqtt: 0.5

devices:
  temp: T
  humi: H
  light: Lu
  led: L
  fan: F
  servo: S

managed_devices:
  temp:
    type: sensor
    unit: celsius
    is_switch: false
    description: Living room temperature
  humi:
    type: sensor
    unit: percent
    is_switch: false
    description: Living room humidity
  light:
    type: sensor
    unit: lux
    is_switch: false
    description: Living room light level
  led:
    type: device
    unit: binary
    is_switch: true
    description: Main LED relay
  fan:
    type: device
    unit: binary
    is_switch: true
    description: Ventilation fan
  servo:
    type: device
    unit: binary
    is_switch: true
    description: Servo actuator (ON/OFF mode)
```

## Chạy

```bash
python GateWay/run.py
```

## Test nhanh

```bash
# Command device (JSON action)
mosquitto_pub -t "home/livingroom/device/led/set" -m '{"action":"on"}'
mosquitto_pub -t "home/livingroom/device/servo/set" -m '{"action":"on"}'

# System get all
mosquitto_pub -t "home/system/getall" -m '{}'

# Subscribe states
mosquitto_sub -t "home/livingroom/sensor/#" -v
mosquitto_sub -t "home/livingroom/device/+/state" -v
mosquitto_sub -t "home/system/stateall" -v
```
