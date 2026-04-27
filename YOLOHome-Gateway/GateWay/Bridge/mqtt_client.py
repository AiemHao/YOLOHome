"""
MQTT Client Module - Chỉ xử lý gửi/nhận dữ liệu từ MQTT broker
Không chứa logic xử lý dữ liệu, chỉ là lớp giao tiếp
"""

import paho.mqtt.client as mqtt
from typing import Callable, List, Optional
import logging

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    MQTT Client để kết nối với MQTT broker
    Callback sử dụng (topic: str, payload: str) -> None
    """
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 1883,
        username: str = "",
        password: str = "",
        sub_topics: Optional[List[str]] = None,
        callback: Optional[Callable[[str, str], None]] = None
    ):
        """
        Khởi tạo MQTT Client
        
        Args:
            host: Địa chỉ MQTT broker
            port: Port MQTT broker (mặc định 1883)
            username: Username để authenticate
            password: Password để authenticate
            sub_topics: Danh sách topics cần subscribe
            callback: Hàm callback khi nhận message (topic, payload) -> None
        """
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1 if hasattr(mqtt, 'CallbackAPIVersion') else None)
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        self.sub_topics = sub_topics or []
        self.on_msg_callback = callback
        self.is_connected = False
        
        # Setup callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Internal callback khi kết nối tới broker thành công hoặc thất bại
        
        Args:
            client: MQTT client instance
            userdata: User data (không sử dụng)
            flags: Connection flags
            rc: Return code (0 = success, khác 0 = failure)
        
        Side Effects:
            - Set is_connected status
            - Auto-subscribe to configured topics
            - Log connection result
        """
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT: Connected to {self.host}:{self.port}")
            
            # Subscribe tới các topics
            for topic in self.sub_topics:
                client.subscribe(topic)
                logger.info(f"MQTT: Subscribed to {topic}")
        else:
            logger.error(f"MQTT: Connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """
        Internal callback khi nhận message từ broker
        
        Args:
            client: MQTT client instance
            userdata: User data (không sử dụng)
            msg: MQTT message object (có .topic và .payload)
        
        Side Effects:
            - Decode message payload
            - Call user-defined callback if set
            - Log errors if callback fails
        
        Note:
            Callback exception được catch để tránh block message loop
        """
        topic = msg.topic
        payload = msg.payload.decode('utf-8', errors='ignore')
        
        logger.debug(f"MQTT: Received from {topic}: {payload}")
        
        if self.on_msg_callback:
            try:
                self.on_msg_callback(topic, payload)
            except Exception as e:
                logger.error(f"MQTT: Error in callback - {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Internal callback khi ngắt kết nối từ broker
        
        Args:
            client: MQTT client instance
            userdata: User data (không sử dụng)
            rc: Return code (0 = client request, khác 0 = unexpected)
        
        Side Effects:
            - Update is_connected status
            - Log disconnection reason
        """
        self.is_connected = False
        if rc != 0:
            logger.warning(f"MQTT: Unexpected disconnection - code {rc}")
        else:
            logger.info("MQTT: Disconnected")
    
    def connect(self):
        """
        Kết nối đồng bộ (blocking) tới MQTT broker
        
        Side Effects:
            - Khởi tạo TCP connection
            - Trigger _on_connect callback khi thành công
        
        Raises:
            Exception: Nếu kết nối thất bại (socket error, DNS, etc.)
        
        Note:
            Sử dụng connect_async() + loop_start() để non-blocking
        """
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            logger.info(f"MQTT: Connecting to {self.host}:{self.port}...")
        except Exception as e:
            logger.error(f"MQTT: Connection error - {e}")
            raise
    
    def connect_async(self):
        """
        Kết nối bất đồng bộ (non-blocking) tới MQTT broker
        
        Side Effects:
            - Khởi tạo async connection
            - Phải gọi loop_start() để xử lý connection
            - Trigger _on_connect callback sau khi connected
        
        Raises:
            Exception: Nếu setup thất bại (invalid host, etc.)
        
        Note:
            Phối hợp với loop_start() để chạy background
            Đây là phương thức được khuyên dùng cho production
        """
        try:
            self.client.connect_async(self.host, self.port, keepalive=60)
            logger.info(f"MQTT: Connecting async to {self.host}:{self.port}...")
        except Exception as e:
            logger.error(f"MQTT: Connection error - {e}")
            raise
    
    def start(self):
        """
        Khởi động kết nối async + background event loop
        
        Side Effects:
            - Gọi connect_async() để thiết lập connection
            - Gọi loop_start() để chạy event loop trong background thread
            - Sau hàm này trả về, kết nối vẫn chạy ở background
        
        Raises:
            Exception: Nếu kết nối thất bại
        
        Usage:
            ```python
            client.start()  # Không block, kết nối chạy ở background
            # Có thể publish/subscribe ở main thread
            client.stop()   # Dừng khi xong
            ```
        """
        self.connect_async()
        self.client.loop_start()
        logger.info("MQTT: Started background loop")
    
    def stop(self):
        """
        Dừng background event loop và ngắt kết nối từ broker
        
        Side Effects:
            - Dừng message processing loop
            - Gửi DISCONNECT packet tới broker
            - Đóng socket connection
            - Set is_connected = False
        
        Note:
            Nên gọi stop() khi shutdown gateway để clean up gracefully
        """
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT: Stopped")
    
    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """
        Publish message tới topic
        
        Args:
            topic: MQTT topic
            payload: Dữ liệu (string)
            qos: Quality of Service (0, 1, hoặc 2)
            retain: Giữ lại message trên broker
        """
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
            logger.debug(f"MQTT: Published to {topic}: {payload}")
        except Exception as e:
            logger.error(f"MQTT: Publish error - {e}")
    
    def subscribe(self, topic: str, qos: int = 0):
        """
        Subscribe tới topic
        
        Args:
            topic: MQTT topic (hỗ trợ wildcards # và +)
            qos: Quality of Service
        """
        try:
            self.client.subscribe(topic, qos=qos)
            logger.info(f"MQTT: Subscribed to {topic}")
        except Exception as e:
            logger.error(f"MQTT: Subscribe error - {e}")
    
    def unsubscribe(self, topic: str):
        """
        Unsubscribe khỏi topic
        
        Args:
            topic: MQTT topic (hỗ trợ wildcards như subscribe)
        
        Side Effects:
            - Gửi UNSUBSCRIBE packet tới broker
            - Broker sẽ không gửi message cho topic này nữa
        
        Raises:
            Exception: Nếu operation thất bại
        """
        try:
            self.client.unsubscribe(topic)
            logger.info(f"MQTT: Unsubscribed from {topic}")
        except Exception as e:
            logger.error(f"MQTT: Unsubscribe error - {e}")
    
    def set_callback(self, callback: Callable[[str, str], None]):
        """
        Đặt hoặc thay đổi hàm callback xử lý message từ broker
        
        Args:
            callback: Hàm có signature (topic: str, payload: str) -> None
                     được gọi khi nhận message mới
        
        Example:
            ```python
            def handle_message(topic, payload):
                print(f"Received: {topic} = {payload}")
            
            client = MQTTClient()
            client.set_callback(handle_message)
            client.start()
            ```
        
        Note:
            Có thể gọi lại để thay đổi callback runtime
        """
        self.on_msg_callback = callback
