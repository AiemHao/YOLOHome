# YOLOHome MQTT API Documentation

Tài liệu này mô tả chuẩn giao tiếp MQTT của YOLOHome Gateway, bao gồm phạm vi API, topic sử dụng, định dạng payload và cơ chế phản hồi.

## 1) Phạm vi và quy ước

- `prefix`: `home`
- `location`: `livingroom`
- Danh sách thiết bị hợp lệ: lấy từ `managed_devices` trong [config.yml](../config.yml)
- Toàn bộ payload MQTT bắt buộc là JSON object hợp lệ

Mẫu topic tổng quát:

`{prefix}/{location}/{device_type}/{property}/{action_or_status}`

## 2) API Gateway lắng nghe (Subscribe)

| API | Mô tả | Request Topic | Request Payload | Response Topic | Response Payload |
|---|---|---|---|---|---|
| Device Command | Nhận lệnh điều khiển thiết bị và chuyển xuống kit qua Serial | `home/livingroom/device/{device}/set` | `{"action":"..."}` | Không phản hồi tức thời | Trạng thái được publish khi kit gửi dữ liệu định kỳ |
| Get All States | Yêu cầu snapshot trạng thái của toàn bộ thiết bị đang quản lý | `home/system/getall` | `{}` | `home/system/stateall` | `{"temp":"25.5","led":"1",...}` |

Lưu ý:
- Chỉ xử lý thiết bị có trong `managed_devices`.
- Lệnh `device/set` không cập nhật state cache ngay lập tức; cache chỉ cập nhật khi có dữ liệu từ kit qua Serial.

## 3) API Gateway phát dữ liệu (Publish)

| API | Mô tả | Publish Topic | Publish Payload | Điều kiện phát |
|---|---|---|---|---|
| Sensor State Publish | Phát dữ liệu cảm biến | `home/livingroom/sensor/{sensor}` | `{"value":"25.5"}` | Khi nhận frame Serial hợp lệ từ cảm biến |
| Device State Publish | Phát trạng thái thiết bị điều khiển | `home/livingroom/device/{device}/state` | `{"action":"on"}` hoặc `{"action":"off"}` | Khi nhận frame Serial hợp lệ từ thiết bị |
| System Snapshot Publish | Phát snapshot trạng thái toàn hệ thống | `home/system/stateall` | `{"temp":"25.5","humi":"60","led":"1",...}` | Khi nhận request `home/system/getall` |

## 4) Đặc tả payload

### 4.1 Device command request

Topic:
- `home/livingroom/device/{device}/set`

Payload bắt buộc:

```json
{
  "action": "..."
}
```

Ví dụ:

```json
{"action":"on"}
{"action":"off"}
```

Quy đổi nội bộ:
- Thiết bị ON/OFF (`is_switch=true`):
  - `on`, `1`, `true` -> Serial value `1`
  - `off`, `0`, `false` -> Serial value `0`

### 4.2 Sensor state publish

Topic:
- `home/livingroom/sensor/{sensor}`

Payload:

```json
{
  "value": "<sensor_value>"
}
```

### 4.3 Device state publish

Topic:
- `home/livingroom/device/{device}/state`

Payload:

```json
{
  "action": "on"
}
```

### 4.4 System snapshot publish

Topic:
- `home/system/stateall`

Payload:

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

## 5) Validation và xử lý lỗi

- Payload không phải JSON object: từ chối xử lý.
- Thiếu trường `action` với topic `device/set`: từ chối xử lý.
- Thiết bị không nằm trong `managed_devices`: bỏ qua request.
- Topic không đúng schema: bỏ qua request.

## 6) Ví dụ luồng end-to-end

1. Ứng dụng gửi lệnh:
   - Topic: `home/livingroom/device/led/set`
   - Payload: `{"action":"on"}`
2. Gateway chuyển lệnh Serial: `!L:1#`
3. Kit phản hồi định kỳ: `!L:1#`
4. Gateway publish trạng thái:
   - Topic: `home/livingroom/device/led/state`
  - Payload: `{"action":"on"}`

## 7) Kiểm thử nhanh bằng mosquitto

Publish request:

```bash
mosquitto_pub -t "home/livingroom/device/led/set" -m '{"action":"on"}'
mosquitto_pub -t "home/livingroom/device/servo/set" -m '{"action":"on"}'
mosquitto_pub -t "home/system/getall" -m '{}'
```

Subscribe response:

```bash
mosquitto_sub -t "home/livingroom/sensor/#" -v
mosquitto_sub -t "home/livingroom/device/+/state" -v
mosquitto_sub -t "home/system/stateall" -v
```
