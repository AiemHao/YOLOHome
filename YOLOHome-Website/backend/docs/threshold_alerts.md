# Đặc tả tính năng cảnh báo ngưỡng trên Web

## 1. Mục tiêu

Tính năng cảnh báo ngưỡng giúp hệ thống thông báo cho người dùng khi dữ liệu cảm biến vượt ngưỡng cấu hình (nhiệt độ, độ ẩm, ánh sáng). Cảnh báo được lưu vào MongoDB và hiển thị trên giao diện Web theo thời gian gần thực (polling).

## 2. Thành phần liên quan

- Backend Node.js: nhận MQTT, kiểm tra ngưỡng, tạo cảnh báo.
- MongoDB: lưu Alert và ThresholdTrace.
- Frontend React: hiển thị cảnh báo, cho phép xác nhận (resolve).

## 3. Luồng hoạt động

1. Gateway publish sensor qua MQTT:
   - home/livingroom/sensor/temp
   - home/livingroom/sensor/humi
   - home/livingroom/sensor/light

2. Backend nhận đủ 3 giá trị cảm biến trong một snapshot.

3. Backend kiểm tra ngưỡng theo config:
   - Đọc từ YOLOHome-Gateway/config.yml (automation.thresholds).
   - Nếu không đọc được, dùng default.

4. Nếu vượt ngưỡng:
   - Tạo Alert trong MongoDB.
   - Ghi ThresholdTrace để audit.

5. Frontend gọi API lấy danh sách cảnh báo active:
   - GET /api/alerts/active (mỗi 5 giây).

6. Người dùng bấm Xác nhận để resolve:
   - PATCH /api/alerts/{id}/resolve

## 4. Dữ liệu và chuẩn hoá ngưỡng

Ngưỡng lấy từ config theo cấu trúc:

automation:
thresholds:
temp: - above: 30
humi: - above: 70
below: 65
light: - below: 30

Các tên ngưỡng map theo tài liệu:

- threshold_mapping.md

## 5. API Backend

### 5.1 Lấy cảnh báo đang active

GET /api/alerts/active

Response 200:
{
"success": true,
"count": 2,
"data": [
{
"_id": "...",
"type": "light",
"severity": "INFO",
"message": "Vượt ngưỡng: Dark Environment. Cảm biến=light, giá trị=25 < 30",
"value": 25,
"threshold": 30,
"condition": "<",
"isResolved": false,
"createdAt": "2026-05-17T10:00:00.000Z"
}
]
}

### 5.2 Resolve cảnh báo

PATCH /api/alerts/{id}/resolve

Response 200:
{
"success": true,
"data": {
"\_id": "...",
"isResolved": true,
"resolvedAt": "2026-05-17T10:05:00.000Z"
}
}

### 5.3 Lấy danh sách cảnh báo (tổng)

GET /api/alerts?isResolved=true|false&limit=50&skip=0

## 6. Schema liên quan

### 6.1 Alert (MongoDB)

- type: temperature | humidity | light | system
- severity: INFO | WARNING | CRITICAL
- message: chuỗi hiển thị
- value: giá trị đo
- threshold: ngưỡng so sánh
- condition: > hoặc <
- isResolved: boolean
- createdAt, resolvedAt

### 6.2 ThresholdTrace (MongoDB)

- sensorType, value, thresholdId, thresholdName
- thresholdValue, triggerDirection, actionTaken
- status, errorMsg

## 7. Quy tắc chống trùng

- Nếu đã tồn tại Alert chưa resolve cho cùng:
  - type + condition + threshold
    thì không tạo thêm.

## 8. Hiển thị trên Frontend

- Dashboard hiển thị khung Cảnh báo ngưỡng khi có ít nhất 1 alert.
- Khi không có alert, khung ẩn.
- Cảnh báo hiển thị nền đỏ nhạt để gây chú ý.

## 9. Lưu ý vận hành

- MQTT clientId không được trùng với Gateway để tránh reconnect liên tục.
- Cần có đủ 3 sensor (temp, humi, light) để hệ thống tạo snapshot và kiểm tra ngưỡng.
- Nếu cần cập nhật ngưỡng, sửa config.yml ở Gateway rồi restart backend để reload.
