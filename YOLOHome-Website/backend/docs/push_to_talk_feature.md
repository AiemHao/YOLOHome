# Tính năng Push-to-Talk (Điều khiển bằng giọng nói)

Tài liệu này mô tả chi tiết về tính năng **Push-to-Talk** được tích hợp trong hệ thống YOLOHome, cho phép người dùng điều khiển các thiết bị nhà thông minh bằng giọng nói tiếng Việt thông qua giao diện Web.

## 1. Tổng quan (Overview)

Tính năng **Push-to-Talk** cung cấp một nút Micro nổi (Floating Action Button) trên giao diện Frontend. Người dùng chỉ cần thao tác **"Nhấn và Giữ" (Hold)** để ghi âm lệnh giọng nói (ví dụ: _"Bật đèn phòng khách"_). Ngay khi nhả chuột, hệ thống sẽ xử lý luồng âm thanh, nhận diện văn bản, phân tích ý định (Intent), gửi lệnh điều khiển tới thiết bị qua giao thức MQTT và lưu lại lịch sử tương tác.

## 2. Kiến trúc hệ thống (Architecture & Workflow)

Luồng xử lý của tính năng được chia làm 4 giai đoạn chính, đi qua các thành phần (Micro-services) khác nhau để đảm bảo hiệu suất và độ chính xác:

### Bước 1: Thu âm tại Frontend (React)

- **Component**: `VoiceControl.js` & `VoiceControl.css`
- **Công nghệ**: Sử dụng thư viện `RecordRTC` kết hợp `MediaDevices API`.
- **Nhiệm vụ**:
  - Cung cấp giao diện trực quan với hiệu ứng **Pulse (lan tỏa đỏ)** khi đang ghi âm và trạng thái **Loading** khi chờ server xử lý.
  - Ghi âm qua Microphone và tự động chuyển đổi chuẩn hóa luồng âm thanh thành định dạng khắt khe: **WAV PCM 16-bit, Mono, 16kHz**.
  - Gói dữ liệu âm thanh vào tệp `.wav` và gửi yêu cầu `POST /api/voice/command` dưới dạng `multipart/form-data` xuống Backend.

### Bước 2: Dàn xếp tại Backend (Node.js / Express)

- **Component**: `voiceRoutes.js`, `voiceService.js`
- **Nhiệm vụ**:
  - Sử dụng middleware `multer` để nhận file âm thanh lưu vào bộ nhớ tạm (Buffer).
  - Đóng vai trò là Nhạc trưởng (Orchestrator) để gọi lần lượt 2 Micro-service AI bằng ngôn ngữ Python.

### Bước 3: Xử lý AI qua Python Micro-services

1. **STT Service (Speech-To-Text) - Port 8500**:
   - Nhận Buffer âm thanh WAV từ Backend.
   - Sử dụng model nhận diện giọng nói **Vosk Tiếng Việt**.
   - Trả về văn bản chuỗi (Transcript). (Ví dụ: _"bật quạt"_)
2. **ML Intent Service (Machine Learning) - Port 8000**:
   - Nhận văn bản Transcript.
   - Dùng mô hình học máy (đã train trên tập dữ liệu điều khiển nhà thông minh) để phân loại ý định.
   - Trả về cấu trúc Intent cụ thể gồm `action` (on/off) và `device` (fan/led/v.v..).

### Bước 4: Thực thi lệnh và Ghi vết (Execution & Traceability)

- Sau khi nhận được Intent, Node.js Backend sẽ map với cấu hình MQTT.
- **MQTT Dispatch**: Gửi message đến MQTT Broker theo topic tương ứng (ví dụ: `home/default/device/led/set`, payload: `ON`).
- **ControlTrace Logging**: Toàn bộ quá trình (kể cả thành công hay lỗi tệp, lỗi nhận diện) đều được lưu trữ tự động vào cơ sở dữ liệu MongoDB thông qua `ControlTrace` Schema để phục vụ việc audit (kiểm tra) và hiển thị trên Dashboard sau này.
- **Phản hồi**: Backend trả kết quả về Frontend hiển thị một Toast (thông báo popup) trực quan cho người dùng.

---

## 3. Cấu trúc thư mục liên quan

- **Frontend**:
  - `YOLOHome-Website/frontend/src/components/VoiceControl.js`
  - `YOLOHome-Website/frontend/src/services/api.js`
- **Backend Node.js**:
  - `YOLOHome-Website/backend/routes/voiceRoutes.js`
  - `YOLOHome-Website/backend/services/voiceService.js`
  - `YOLOHome-Website/backend/models/ControlTrace.js`
- **Python STT**:
  - `YOLOHome-Website/backend/stt_service/vosk_server.py`
- **Python ML Intent**:
  - `YOLOHome-Website/backend/ml_service/ml_server.py`

---

## 4. Đặc tả chạy thử và lệnh cần chạy (Run Guide)

### 4.1 Yêu cầu trước khi chạy

- Docker chứa MQTT và Mongo đang chạy.
- Các model đã có sẵn:
  - Vosk: `vosk-model-vn-0.4`
  - Intent model: `intent_model.pkl`

### 4.2 Mở 4 tab Terminal và chạy theo thứ tự

1. **Tab 1 - Vosk STT Server**

```bash
cd D:\STUDY\DADN\YOLOHome\YOLOHome-Website\backend\stt_service
$env:VOSK_MODEL_PATH="d:\STUDY\DADN\YOLOHome\YOLOHome-Gateway\GateWay\Voice\models\vosk-model-vn-0.4"
uvicorn vosk_server:app --reload --port 8500
```

2. **Tab 2 - ML Intent Server**

```bash
cd D:\STUDY\DADN\YOLOHome\YOLOHome-Website\backend\ml_service
$env:MODEL_PATH="d:\STUDY\DADN\YOLOHome\YOLOHome-Gateway\GateWay\Voice\models\intent_model.pkl"
uvicorn ml_server:app --reload --port 8000
```

3. **Tab 3 - Backend Node.js**

```bash
cd D:\STUDY\DADN\YOLOHome\YOLOHome-Website\backend
$env:VOSK_SERVER_URL="http://localhost:8500/transcribe"
$env:ML_SERVICE_URL="http://localhost:8000/predict"
npm run dev
```
**Lưu ý**: Nếu gặp trường hợp MQTT reconnecting...(Log này cho thấy backend chạy OK, nhưng MQTT đang reconnect liên tục ⇒ broker MQTT không chạy hoặc không kết nối được. Khi bấm giữ nói, backend vẫn xử lý STT/ML, nhưng đến bước publish MQTT sẽ lỗi “MQTT client not connected”, từ đó frontend báo “Gửi lệnh giọng nói thất bại”) thì hãy xem phần 5.1 
4. **Tab 4 - Frontend React**

```bash
cd D:\STUDY\DADN\YOLOHome\YOLOHome-Website\frontend
npm start
```



### 4.3 Kiểm tra nhanh trước khi thử nói

- Backend: `http://localhost:5000/health` trả JSON OK.
- Vosk: `http://localhost:8500/docs` mở được.
- ML Intent: `http://localhost:8000/docs` mở được.

---

## 5. Lưu ý và lỗi thường gặp

### 5.1 Lỗi "Gửi lệnh giọng nói thất bại"

Nguyên nhân thường gặp: Backend không kết nối được MQTT hoặc bị ngắt kết nối liên tục.

- Dấu hiệu: log backend liên tục hiện `MQTT reconnecting...`
- Cách khắc phục:
  - Đảm bảo MQTT broker đang chạy trên `mqtt://localhost:1883`.
  - Đặt `MQTT_CLIENT_ID` khác nhau cho từng tiến trình (Backend và Gateway không được trùng).
  - Khởi động lại backend sau khi đổi `MQTT_CLIENT_ID`.

### 5.2 Lỗi "Intent not recognized"

- Đảm bảo ML Intent server đang chạy và `MODEL_PATH` đúng.
- Kiểm tra model `intent_model.pkl` đã tồn tại và được load thành công.

### 5.3 Không nhận diện được giọng nói (No speech recognized)

- Kiểm tra quyền microphone của trình duyệt.
- Đảm bảo audio là WAV PCM 16-bit, Mono, 16kHz (frontend đã cấu hình sẵn).
- Kiểm tra log Vosk server để xác nhận có nhận file audio.

---

## 6. Ghi chú triển khai

- Hệ thống hiện chỉ sử dụng **Vosk** để nhận diện giọng nói.
- Các cấu hình liên quan Whisper/Google đã được loại bỏ để tránh nhầm lẫn.
