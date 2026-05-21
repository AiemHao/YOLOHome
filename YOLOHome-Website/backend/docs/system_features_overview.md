# Tổng quan 3 tài liệu tính năng (High-Level)

Tài liệu này tổng hợp nhanh 3 thành phần chính trong thư mục docs, tập trung vào: nó là gì, dùng để làm gì, luồng hoạt động, và kết quả/đầu ra.

---

## 1. Push-to-Talk (Điều khiển bằng giọng nói)

### Nó là gì?

Chức năng điều khiển thiết bị bằng giọng nói tiếng Việt trên giao diện Web, thông qua nút nhấn-giữ để ghi âm.

### Dùng để làm gì?

Cho phép người dùng nói lệnh (bật/tắt thiết bị), hệ thống tự nhận diện giọng nói và gửi lệnh điều khiển qua MQTT.

### Luồng hoạt động (Flow)

1. Frontend ghi âm WAV PCM 16-bit, 16kHz rồi gửi `POST /api/voice/command`.
2. Backend nhận file, gọi lần lượt 2 dịch vụ Python:
   - STT (Speech-to-Text) để chuyển giọng nói thành văn bản.
   - ML Intent để phân loại ý định (action + device).
3. Backend map intent sang lệnh MQTT và gửi đi.
4. Ghi log vào `ControlTrace` và trả kết quả về frontend.

### Kết quả / Cách sử dụng

- Người dùng nhấn giữ nút mic trên UI để nói lệnh.
- Kết quả trả về là toast thông báo thành công/không thành công.
- Dịch vụ phụ trợ:
  - STT: `http://localhost:8500/docs`
  - ML Intent: `http://localhost:8000/docs`
  - Backend health: `http://localhost:5000/health`

### Hạn chế / Vấn đề hiện tại (Optional)

- Phụ thuộc vào STT/ML chạy ổn định; dễ lỗi nếu thiếu model hoặc port bận.
- Độ chính xác intent phụ thuộc dataset train hiện tại.

### Hướng cải thiện (Optional)

- Bổ sung cơ chế retry/timeout rõ ràng giữa backend và STT/ML.
- Mở rộng dữ liệu train để giảm lỗi “Intent not recognized”.

---

## 2. Cảnh báo ngưỡng (Threshold Alerts)

### Nó là gì?

Cơ chế cảnh báo khi cảm biến vượt ngưỡng cấu hình (nhiệt độ/độ ẩm/ánh sáng), hiển thị trên web và lưu lịch sử.

### Dùng để làm gì?

Giúp người dùng nhận biết sớm tình trạng bất thường của môi trường (nóng, ẩm, tối, sáng quá mức).

### Luồng hoạt động (Flow)

1. Gateway gửi dữ liệu sensor qua MQTT theo từng loại.
2. Backend gom đủ 3 sensor tạo snapshot.
3. Backend so sánh với ngưỡng trong config.
4. Nếu vượt ngưỡng:
   - Tạo Alert trong MongoDB.
   - Ghi `ThresholdTrace` để audit.
5. Frontend polling `GET /api/alerts/active` mỗi 5 giây.
6. Người dùng có thể `PATCH /api/alerts/{id}/resolve` để xác nhận.

### Kết quả / Cách sử dụng

- Alert hiển thị trên dashboard khi có cảnh báo active.
- Các API chính:
  - `GET /api/alerts/active`
  - `PATCH /api/alerts/{id}/resolve`
  - `GET /api/alerts?isResolved=true|false`

### Hạn chế / Vấn đề hiện tại (Optional)

- Cần đủ cả 3 sensor mới tạo snapshot; thiếu 1 sensor sẽ không kiểm tra ngưỡng.
- Cơ chế polling mỗi 5 giây có thể chưa “real-time”.

### Hướng cải thiện (Optional)

- Chuyển sang WebSocket/SSE để cập nhật cảnh báo realtime.
- Cho phép cấu hình ngưỡng trực tiếp từ UI thay vì sửa file config.

---

## 3. Threshold Mapping

### Nó là gì?

Bảng ánh xạ giữa `thresholdId` nội bộ và tên/miêu tả dễ hiểu cho người dùng.

### Dùng để làm gì?

Chuẩn hóa thông tin hiển thị/log, giúp log `ThresholdTrace` có tên rõ ràng.

### Luồng hoạt động (Flow)

1. Khi phát hiện vượt ngưỡng, backend chọn `thresholdId`.
2. Ánh xạ sang `thresholdName` dựa trên bảng mapping.
3. Ghi vào log và hiển thị cho người dùng.

### Kết quả / Cách sử dụng

- Dùng làm tài liệu tham chiếu cho log `ThresholdTrace`.
- Ví dụ: `temp_high` -> “High Temperature”.

### Hạn chế / Vấn đề hiện tại (Optional)

- Mapping đang viết tay, dễ lệch so với config thực tế.

### Hướng cải thiện (Optional)

- Tự sinh mapping từ config hoặc lưu mapping trong DB để cập nhật linh hoạt.
