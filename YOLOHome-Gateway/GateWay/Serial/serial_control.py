"""
Serial Module - Chỉ xử lý gửi/nhận dữ liệu từ serial port
Không chứa logic xử lý dữ liệu, chỉ là lớp giao tiếp
"""

import serial
import logging
from typing import Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)


class SerialModule:
    """
    Serial Module để giao tiếp với kit thông qua COM port
    Hỗ trợ callback khi nhận dữ liệu
    """
    
    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1,
        callback: Optional[Callable[[str], None]] = None
    ):
        """
        Khởi tạo Serial Module
        
        Args:
            port: COM port (ví dụ: "COM3")
            baudrate: Baud rate (mặc định 115200)
            timeout: Timeout cho read/write (giây)
            callback: Hàm callback khi nhận dữ liệu từ kit
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.on_data_callback = callback
        self.is_running = False
        self._reader_thread = None
        
        self._connect()
    
    def _connect(self):
        """Kết nối tới COM port"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            logger.info(f"Serial: Connected to {self.port} at {self.baudrate} bps")
            time.sleep(0.5)  # Chờ để kit ready
        except serial.SerialException as e:
            logger.error(f"Serial: Connection failed - {e}")
            self.ser = None
            raise
    
    def disconnect(self):
        """Ngắt kết nối"""
        self.stop_reading()
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Serial: Disconnected")
    
    def send_packet(self, packet: str) -> bool:
        """
        Gửi packet đã format sẵn tới kit qua Serial
        Format phải được chuẩn bị trước bởi Adapter
        
        Args:
            packet: Packet đã format (ví dụ: "!LED:1#")
        
        Returns:
            True nếu gửi thành công, False nếu lỗi
        """
        if not self.ser or not self.ser.is_open:
            logger.warning("Serial: Not connected")
            return False
        
        try:
            self.ser.write(packet.encode('utf-8'))
            logger.debug(f"Serial: Sent packet: {packet}")
            return True
        except Exception as e:
            logger.error(f"Serial: Send error - {e}")
            return False
    
    def read_data(self) -> Optional[str]:
        """
        Đọc một dòng dữ liệu từ serial
        
        Returns:
            Chuỗi dữ liệu nếu có, None nếu không
        """
        if not self.ser or not self.ser.is_open:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    logger.debug(f"Serial: Received: {line}")
                    return line
        except Exception as e:
            logger.error(f"Serial: Read error - {e}")
        
        return None
    
    def start_reading(self):
        """Bắt đầu thread đọc dữ liệu background"""
        if self.is_running:
            logger.warning("Serial: Already reading")
            return
        
        if not self._reader_thread or not self._reader_thread.is_alive():
            self.is_running = True
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            logger.info("Serial: Started background reading")
    
    def stop_reading(self):
        """Dừng thread đọc dữ liệu"""
        self.is_running = False
        if self._reader_thread:
            self._reader_thread.join(timeout=2)
        logger.info("Serial: Stopped reading")
    
    def _read_loop(self):
        """Loop đọc dữ liệu liên tục"""
        while self.is_running:
            data = self.read_data()
            if data and self.on_data_callback:
                try:
                    self.on_data_callback(data)
                except Exception as e:
                    logger.error(f"Serial: Callback error - {e}")
            time.sleep(0.01)  # Tránh busy-waiting
    
    def set_callback(self, callback: Callable[[str], None]):
        """Đặt callback xử lý dữ liệu nhận được"""
        self.on_data_callback = callback
    
    def clear_buffer(self):
        """Xóa buffer nhận/gửi"""
        if self.ser and self.ser.is_open:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            logger.info("Serial: Cleared buffers")