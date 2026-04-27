# YOLOHome Backend

Backend API cho hệ thống YOLOHome, xây dựng bằng Express + MongoDB + MQTT.

## 1. Công nghệ sử dụng

- Node.js (ES Modules)
- Express
- Mongoose
- MQTT.js
- Nodemon

## 2. Kiến trúc code

```text
backend/
├─ config/          # config app, db, mqtt
├─ constants/       # constants dùng chung
├─ controllers/     # xử lý request/response
├─ middleware/      # logging, error handler
├─ models/          # MongoDB schemas
├─ routes/          # định nghĩa endpoint
├─ services/        # business logic
│  └─ mqtt/         # module MQTT riêng
└─ server.js        # entrypoint
```

## 3. Cài đặt và chạy

### Cài dependencies

```bash
npm install
```

### Tạo file `.env`

Tạo file `.env` trong thư mục `backend` với nội dung mẫu:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/yolohome?retryWrites=true&w=majority

PORT=5000
NODE_ENV=development
CORS_ORIGIN=*

MQTT_ENABLED=true
MQTT_BROKER_URL=mqtt://localhost:1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=yolohome-backend
MQTT_QOS=1
MQTT_RETAIN=false
```

### Chạy server

```bash
npm run dev
```

Hoặc:

```bash
npm start
```

## 4. MQTT topic structure

Theo chuẩn YOLOHome:

- Tất cả topic MQTT được hardcode tập trung trong `services/mqtt/mqttTopics.js`.
- Sensor subscribe: `home/+/sensor/+`
- Device state subscribe: `home/+/device/+/state`
- System subscribe: `home/system/+`
- Device command publish: `home/livingroom/device/{type}/set`
- System action publish: `home/system/{action}`

Ví dụ:

- `home/livingroom/sensor/temp`
- `home/livingroom/device/led/set`
- `home/livingroom/device/led/state`
- `home/system/getall`

Timeout chờ phản hồi MQTT ở backend đang cố định 5 giây.

Payload chuẩn gateway:

- Device command (`.../device/{type}/set`): `{"action":"on|off|..."}`
- System get all (`home/system/getall`): `{}`
- Sensor state (`.../sensor/{type}`): `{"value":"..."}`
- Device state (`.../device/{type}/state`): `{"action":"on|off"}`
- System snapshot (`home/system/stateall`): `{"temp":"25.5","humi":"60","light":"700","led":"1",...}`

## 5. API Docs

Xem tài liệu endpoint chi tiết tại `API_DOCS.md`.

## 6. Lưu ý hiện tại

- Password user đang lưu plain text (chưa hash).
- Chưa có JWT auth.
