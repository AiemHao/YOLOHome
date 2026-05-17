# YOLOHome Gateway Test Suite

Test cases cho các thành phần chính của YOLOHome Gateway.

## Cấu trúc test

- `test_threshold_service.py`: Test cases cho ThresholdService
- `test_controller_threshold.py`: Test cases cho threshold integration trong MainController

## Cách chạy test

### Chạy tất cả test:
```bash
cd YOLOHome-Gateway/GateWay/tests
python -m unittest discover
```

### Chạy test cụ thể:
```bash
# Test ThresholdService
python -m unittest test_threshold_service.py

# Test Controller threshold integration
python -m unittest test_controller_threshold.py
```

### Chạy với verbose output:
```bash
python -m unittest discover -v
```

## Coverage

Test cases bao gồm:

### ThresholdService:
- ✅ Khởi tạo service
- ✅ Bật/tắt threshold automation
- ✅ Trigger threshold khi sensor > above
- ✅ Trigger threshold khi sensor < below
- ✅ Không trigger khi trong range
- ✅ Không trigger khi disabled
- ✅ Handle invalid sensor values
- ✅ Handle unknown sensors
- ✅ Normalize threshold values
- ✅ Update rules runtime
- ✅ Get status
- ✅ Multiple sensors control cùng device

### MainController Threshold Integration:
- ✅ Khởi tạo threshold service
- ✅ Bật/tắt threshold qua controller
- ✅ Get threshold status
- ✅ Threshold trigger trong serial callback
- ✅ Không trigger khi disabled
- ✅ Không trigger khi trong range
- ✅ Trigger below threshold
- ✅ Rate limiting
- ✅ Chỉ trigger cho sensor devices
- ✅ Handle invalid values
- ✅ Handle unknown target devices
- ✅ Update rules runtime

## Thêm test case mới

1. Tạo file `test_<component>.py`
2. Import unittest và các module cần test
3. Tạo class kế thừa `unittest.TestCase`
4. Viết test methods với prefix `test_`
5. Sử dụng assertions để verify behavior

Ví dụ:
```python
import unittest
from ..module import Component

class TestComponent(unittest.TestCase):
    def test_feature(self):
        component = Component()
        result = component.do_something()
        self.assertEqual(result, expected_value)
```