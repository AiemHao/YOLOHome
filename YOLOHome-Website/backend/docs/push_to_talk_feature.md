# Tính năng Push-to-Talk (Điều khiển bằng giọng nói)

Tài liệu này mô tả chi tiết về tính năng **Push-to-Talk** được tích hợp trong hệ thống YOLOHome, cho phép người dùng điều khiển các thiết bị nhà thông minh bằng giọng nói tiếng Việt thông qua giao diện Web.

## 1. Tổng quan (Overview)
Tính năng **Push-to-Talk** cung cấp một nút Micro nổi (Floating Action Button) trên giao diện Frontend. Người dùng chỉ cần thao tác **"Nhấn và Giữ" (Hold)** để ghi âm lệnh giọng nói (ví dụ: *"Bật đèn phòng khách"*). Ngay khi nhả chuột, hệ thống sẽ xử lý luồng âm thanh, nhận diện văn bản, phân tích ý định (Intent), gửi lệnh điều khiển tới thiết bị qua giao thức MQTT và lưu lại lịch sử tương tác.

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
   - Trả về văn bản chuỗi (Transcript). (Ví dụ: *"bật quạt"*)
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

## 4. Hướng dẫn khởi chạy (Run Guide)
Để tính năng này hoạt động toàn diện, môi trường local cần phải chạy song song 4 tiến trình (Yêu cầu bật Docker chứa broker `mqtt` và `mongo` trước):

1. **Khởi chạy Vosk STT Micro-service**:
   ```bash
   cd YOLOHome-Website/backend/stt_service
   $env:VOSK_MODEL_PATH="<Đường_dẫn_tuyệt_đối_tới_thư_mục_vosk-model-vn>"
   uvicorn vosk_server:app --reload --port 8500
   ```

2. **Khởi chạy ML Intent Micro-service**:
   ```bash
   cd YOLOHome-Website/backend/ml_service
   uvicorn ml_server:app --reload --port 8000
   ```

3. **Khởi chạy Node.js Backend**:
   ```bash
   cd YOLOHome-Website/backend
   npm run dev
   ```

4. **Khởi chạy React Frontend**:
   ```bash
   cd YOLOHome-Website/frontend
   npm start
   ```

**Lưu ý quan trọng**: Không được để container `yolohome-backend` trong Docker Compose chạy đồng thời với lệnh `npm run dev` ở ngoài môi trường Window để tránh xung đột Port `5000`. Bạn có thể tắt container bằng lệnh `docker stop yolohome-backend`.

---

## 5. Hướng dẫn chuyển đổi mô hình nhận diện (STT Provider)
Hệ thống được thiết kế linh hoạt cho phép chuyển đổi qua lại giữa 3 lõi nhận diện giọng nói: **Vosk (Offline)**, **Whisper (OpenAI)** và **Google Cloud STT**.
Để chuyển đổi, bạn chỉ cần thay đổi file `.env` ở thư mục `YOLOHome-Website/backend/.env` và khởi động lại Node.js Backend.

### 5.1. Sử dụng Vosk (Mặc định - Chạy Offline Local)
Đảm bảo bạn có cấu hình sau trong file `.env`:
```env
STT_PROVIDER=vosk
```
- **Yêu cầu**: Tiến trình `vosk_server.py` ở port `8500` phải đang chạy.

### 5.2. Sử dụng OpenAI Whisper (Chất lượng cao - Cloud)
Sửa file `.env`:
```env
STT_PROVIDER=whisper
WHISPER_API_KEY=sk-xxxx_your_openai_api_key_xxxx
```
- **Lưu ý**: Vì ở Frontend chúng ta đã đổi định dạng ghi âm sang `audio/wav`, bạn cần cập nhật nhỏ trong file `backend/utils/sttProvider.js` ở hàm `transcribeWithWhisper`:
  Sửa `filename: 'audio.webm', contentType: 'audio/webm'` thành `filename: 'audio.wav', contentType: 'audio/wav'`.

### 5.3. Sử dụng Google Speech-to-Text (Cloud)
Sửa file `.env`:
```env
STT_PROVIDER=google
GOOGLE_STT_API_KEY=xxxx_your_google_cloud_api_key_xxxx
```
- **Lưu ý**: Tương tự như Whisper, vì định dạng Frontend gửi lên là WAV PCM, hãy mở file `backend/utils/sttProvider.js` ở hàm `transcribeWithGoogle` và sửa `config` thành:
  ```javascript
  config: {
    encoding: 'LINEAR16',
    sampleRateHertz: 16000,
    languageCode: 'vi-VN',
  }
  ```
