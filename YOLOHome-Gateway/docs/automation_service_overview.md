# Automation Service Overview

Tài liệu này mô tả nhanh hai thành phần tự động hóa chính của Gateway: Threshold Service và AI Service. Nội dung tập trung vào: nó là gì, dùng để làm gì, luồng hoạt động, kết quả/đầu ra, và một vài hạn chế hiện tại.

---

## 1. Threshold Service

### Nó là gì?
Threshold Service là thành phần tự động hóa rule-based của Gateway. Nó dùng để kiểm tra các giá trị sensor so với cấu hình ngưỡng và tự động gửi lệnh điều khiển tới thiết bị tương ứng.

### Dùng để làm gì?
- Tự động bật/tắt thiết bị khi sensor vượt giá trị `above` hoặc `below` cấu hình.
- Hỗ trợ các kịch bản đơn giản như: bật quạt khi nhiệt độ cao, tắt đèn khi ánh sáng đủ, đóng/mở thiết bị dựa trên độ ẩm.
- Giữ cho hệ thống hoạt động tự động mà không cần can thiệp tay.

### Luồng hoạt động (Flow)
1. Gateway khởi tạo Threshold Service với cấu hình ngưỡng từ file config hoặc tham số khởi chạy.
2. Khi có dữ liệu sensor mới, Gateway gọi Threshold Service để kiểm tra rule cho sensor đó.
3. Threshold Service so sánh giá trị sensor với các ngưỡng `above` / `below` của từng rule.
4. Nếu điều kiện rule đạt, nó xác định giá trị lệnh `on_value` hoặc `off_value` cho thiết bị.
5. Service gửi lệnh điều khiển tới command queue của Gateway để thực thi.

### Kết quả / Cách sử dụng
- Kết quả là hệ thống tự động điều khiển thiết bị theo rule đã cấu hình.
- APIs nội bộ chính:
  - `set_enabled(enabled: bool)`: bật/tắt tự động hóa Threshold.
  - `is_enabled() -> bool`: kiểm tra trạng thái Threshold hiện tại.
  - `check_threshold(sensor_name, value, send_command_callback)`: kiểm tra rule với giá trị sensor và gọi callback nếu cần gửi lệnh.
  - `update_rules(rules)`: cập nhật danh sách rule runtime.
- Rule được cấu hình dưới dạng `sensor -> danh sách thiết bị + điều kiện + giá trị lệnh`, và Gateway gọi `check_threshold(...)` mỗi khi một sensor mới cập nhật.

### Hạn chế / Vấn đề hiện tại
- Chỉ xử lý logic rule đơn giản, không có cơ chế học từ dữ liệu.
- Khi cả `above` và `below` cùng tồn tại, hệ thống đang dùng logic “ngoài khoảng”:
  - Chỉ kích hoạt khi giá trị **nhỏ hơn `below` hoặc lớn hơn `above`**
  - Không làm gì khi giá trị nằm trong khoảng giữa  
  → Cách này đôi khi không phù hợp với kỳ vọng về **vùng đệm ngưỡng (tránh bật/tắt liên tục)** hoặc dải trung tính.
- Không có cơ chế xử lý sự biến động liên tục của sensor, dễ gây nhiều lệnh bật/tắt nếu giá trị dao động quanh ngưỡng.

### Hướng cải thiện (Optional)
- Bổ sung cấu hình **vùng đệm ngưỡng (dual-threshold)** rõ ràng để tránh hiện tượng dao động bật/tắt liên tục.
- Cho phép điều chỉnh rule runtime qua giao diện hoặc API.
- Thêm giám sát trạng thái rule và cảnh báo khi cấu hình sai.

---

## 2. AI Curtain Control

### Nó là gì?
AI Curtain Control là thành phần tự động hóa dựa trên mô hình học máy của Gateway, chuyên dùng để điều khiển rèm/servo. Thay vì dùng rule cố định, nó dùng Decision Tree đã huấn luyện để dự đoán hành động mở/đóng từ nhiều sensor cùng lúc.

### Dùng để làm gì?
- Cung cấp tự động hóa thông minh hơn cho điều khiển rèm/cửa dựa trên môi trường.
- Hiện tại tập trung vào điều khiển cửa rèm/servo với sensor `light`, `temp`, `humi`.
- Cho phép quyết định mở/đóng thiết bị dựa trên trạng thái môi trường tổng thể thay vì chỉ một điều kiện đơn lẻ.

### Luồng hoạt động (Flow)
1. Gateway khởi tạo AI Curtain Control với đường dẫn tới model Decision Tree đã huấn luyện.
2. Khi đủ dữ liệu sensor cần thiết, Gateway tạo `sensor_dict` và gọi `check_and_trigger(sensor_dict, send_command_callback)`.
3. AI Curtain Control xác thực sensor và gọi mô hình để dự đoán hành động.
4. Mô hình trả về hành động `0` hoặc `1` tương ứng với đóng/mở.
5. Nếu hành động khác với trạng thái đã gửi trước đó, AI Curtain Control gọi callback để gửi lệnh điều khiển.

### Kết quả / Cách sử dụng
- Kết quả là một lệnh điều khiển rèm/servo được gửi dựa trên dự đoán mô hình.
- APIs nội bộ chính:
  - `check_and_trigger(sensor_dict, send_command_callback)`: chạy dự đoán và gửi lệnh nếu cần.
  - `predict_action(sensor_dict) -> Optional[int]`: trả về `0` hoặc `1` khi dự đoán thành công.
  - `is_enabled() -> bool`: kiểm tra xem AI Curtain Control có bật và model đã load.
  - `get_status()`: trả thông tin trạng thái, model đã load hay chưa, đường dẫn model, và action cuối.
  - `get_model_info()`: trả metadata của mô hình Decision Tree khi đã load.
- Mô hình được lưu dưới dạng pickle và có thể được tạo lại từ script huấn luyện nếu cần.

### Hạn chế / Vấn đề hiện tại
- Chỉ hỗ trợ một mục tiêu hiện tại (`servo`) và bộ sensor cố định (`light`, `temp`, `humi`).
- Nếu thiếu sensor hoặc model chưa tải được, AI Curtain Control không thực hiện và hệ thống sẽ fallback sang Threshold.
- Mô hình phụ thuộc dữ liệu huấn luyện có thể là synthetic, nên chưa thực sự phản ánh điều kiện thực tế.

### Hướng cải thiện (Optional)
- Làm cho mục tiêu điều khiển (`target_device`) và danh sách sensor required configurable.
- Thêm cơ chế reload model runtime và kiểm tra integrity/version model.
- Kết hợp AI Curtain Control với rule-based fallback để hệ thống vẫn hoạt động khi model không khả dụng.