# YOLOHome Backend API Docs

Base URL (local):

```text
http://localhost:5000
```

## 1. Health Check

### GET `/health`

Kiểm tra trạng thái server.

Response `200`:

```json
{
  "status": "OK",
  "message": "Server Backend YOLOHome is running...",
  "timestamp": "2026-03-29T10:00:00.000Z"
}
```

## 2. User APIs

### POST `/api/users/signup`

Tạo tài khoản mới.

Request body:

```json
{
  "username": "admin",
  "password": "123456",
  "fullName": "Administrator"
}
```

Response `201`:

```json
{
  "success": true,
  "message": "Đăng ký tài khoản thành công!",
  "data": {
    "username": "admin",
    "fullName": "Administrator",
    "createdAt": "2026-03-29T10:00:00.000Z"
  }
}
```

Response lỗi:

- `400`: thiếu username/password hoặc username đã tồn tại

### POST `/api/users/login`

Đăng nhập.

Request body:

```json
{
  "username": "admin",
  "password": "123456"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Đăng nhập thành công!",
  "data": {
    "username": "admin",
    "fullName": "Administrator",
    "createdAt": "2026-03-29T10:00:00.000Z"
  }
}
```

Response lỗi:

- `400`: thiếu username/password
- `404`: user không tồn tại
- `401`: sai mật khẩu

## 3. Device APIs

### GET `/api/devices/latest`

Lấy danh sách thiết bị.

Response `200`:

```json
{
  "success": true,
  "data": [
    {
      "deviceName": "Light",
      "status": "on",
      "lastUpdated": "2026-03-29T10:00:00.000Z"
    },
    {
      "deviceName": "Fan",
      "status": "off",
      "lastUpdated": "2026-03-29T10:00:00.000Z"
    },
    {
      "deviceName": "Servo",
      "status": "on",
      "lastUpdated": "2026-03-29T10:00:00.000Z"
    }
  ]
}
```

### POST `/api/devices/control`

Gửi lệnh điều khiển thiết bị qua MQTT theo chuẩn gateway.

Request body:

```json
{
  "deviceName": "Light",
  "deviceType": "led",
  "action": "on"
}
```

Ghi chú:

- Cần `deviceName` hoặc `deviceType`.
- Cần `action` (hoặc `status` để backend map sang `action`).
- `deviceType` mặc định lấy theo `deviceName` nếu không truyền.
- Backend publish lệnh và trả response ngay, không chờ MQTT phản hồi.
- MQTT publish payload gửi tới gateway luôn có dạng: `{"action":"..."}`.
- Topic publish device command được cố định: `home/livingroom/device/{device}/set`.
- Backend không cập nhật DB ngay sau khi gửi lệnh; trạng thái được đồng bộ khi gateway publish `device/{device}/state`.

Response `200`:

```json
{
  "success": true,
  "data": {
    "device": "Light",
    "action": "on",
    "accepted": true
  }
}
```

Response lỗi:

- `400`: thiếu định danh thiết bị hoặc thiếu action/status

## 4. Sensor APIs

### GET `/api/sensors/latest`

Lấy snapshot 3 cảm biến tại timestamp gần nhất.

Response `200`:

```json
{
  "success": true,
  "data": {
    "temperature": 25.5,
    "humidity": 60,
    "light": 700,
    "timestamp": "2026-03-29T10:00:00.000Z"
  }
}
```

## 5. System APIs

### GET `/api/system/getall`

Gửi action hệ thống `getall` qua MQTT topic `home/system/getall`.

Request body: không dùng

Response `200`:

```json
{
  "success": true,
  "data": {
    "temp": "25.5",
    "humi": "60",
    "light": "700",
    "led": "1",
    "fan": "0",
    "servo": "1"
  }
}
```

Ghi chú:

- Backend publish `home/system/getall` với payload `{}`.
- Backend luôn đợi message từ topic `home/system/stateall` trong timeout 5 giây.

Response lỗi:

- `504`: Gateway response timeout

## 6. MQTT mapping

- Sensor data vào: `home/{room}/sensor/{type}`
- Device command ra: `home/{room}/device/{type}/set`
- Device state vào: `home/{room}/device/{type}/state`
- System action ra/vào: `home/system/{action}`

## 7. Error response chuẩn

Lỗi validation/business thường trả:

```json
{
  "success": false,
  "message": "..."
}
```

Lỗi từ global error handler:

```json
{
  "success": false,
  "message": "...",
  "error": "...",
  "timestamp": "2026-03-29T10:00:00.000Z"
}
```
