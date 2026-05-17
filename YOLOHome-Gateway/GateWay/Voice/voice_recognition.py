import os
import sys
import time
import json
import logging
import threading
import traceback
import queue

import numpy as np
import pyaudio

try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    logging.warning("Vosk module not found. Voice feature will be disabled.")
    Model = None
    KaldiRecognizer = None

try:
    import joblib
except ImportError:
    logging.warning("joblib module not found. Cannot load ML intent model.")
    joblib = None

logger = logging.getLogger(__name__)

class VoiceController:
    """
    Lắng nghe microphone, dùng model Vosk (STT) để chuyển giọng nói thành văn bản,
    và dùng model scikit-learn (ML) để phân loại ý định (Intent),
    sau đó publish MQTT để điều khiển thiết bị.
    """
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.running = False
        self.q = queue.Queue()
        
        # Đường dẫn tới thư mục models
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(current_dir, "models")
        self.vosk_model_path = os.path.join(self.models_dir, "vosk-model-vn-0.4")
        self.intent_model_path = os.path.join(self.models_dir, "intent_model.pkl")
        
        self.vosk_model = None
        self.intent_model = None
        
        # Audio Config cho Vosk
        self.RATE = 16000
        self.CHUNK = 8000
        
        self._load_models()

    def _load_models(self):
        """Tải các model cần thiết (Vosk STT và Scikit-learn Intent)"""
        # 1. Load Vosk Model
        if Model is not None:
            if os.path.exists(self.vosk_model_path):
                try:
                    logger.info(f"Loading Vosk model from: {self.vosk_model_path}")
                    # Chặn log của vosk in ra màn hình
                    from vosk import SetLogLevel
                    SetLogLevel(-1) 
                    self.vosk_model = Model(self.vosk_model_path)
                    logger.info("✓ Vosk model loaded successfully")
                except Exception as e:
                    logger.error(f"Error loading Vosk model: {e}")
            else:
                logger.warning(f"Vosk model not found at {self.vosk_model_path}.")
                logger.warning("Please download vosk-model-vn-0.4 and extract it to GateWay/Voice/models/")
        
        # 2. Load Intent Model (ML)
        if joblib is not None:
            if os.path.exists(self.intent_model_path):
                try:
                    logger.info(f"Loading Intent model from: {self.intent_model_path}")
                    self.intent_model = joblib.load(self.intent_model_path)
                    logger.info("✓ Intent model loaded successfully")
                except Exception as e:
                    logger.error(f"Error loading Intent model: {e}")
            else:
                logger.warning(f"Intent model not found at {self.intent_model_path}.")
                logger.warning("Please run train_intent_model.ipynb in notebooks/ to generate it.")

    def _publish_command(self, device, action):
        """Gửi lệnh MQTT tương ứng"""
        if not self.mqtt_client:
            return
            
        topic = f"home/livingroom/device/{device}/set"
        payload = json.dumps({"action": action})
        
        try:
            self.mqtt_client.publish(topic, payload)
            logger.info(f"[VOICE] Đã nhận diện và publish: {topic} {payload}")
        except Exception as e:
            logger.error(f"[VOICE] Lỗi khi publish MQTT: {e}")

    def _process_text(self, text):
        """Phân tích văn bản thành ý định (Intent) dùng ML Model"""
        text = text.lower().strip()
        if not text:
            return
            
        logger.info(f"[VOICE] Bạn vừa nói: '{text}'")
        
        if not self.intent_model:
            logger.warning("[VOICE] Intent model chưa được load, không thể xử lý lệnh.")
            return
            
        try:
            # Dự đoán lệnh
            prediction = self.intent_model.predict([text])[0]
            
            # Lấy độ tin cậy (confidence)
            probabilities = self.intent_model.predict_proba([text])[0]
            confidence = max(probabilities)
            
            # Chỉ thực hiện nếu độ tin cậy > 40% (có thể tùy chỉnh)
            if confidence > 0.40:
                logger.info(f"[VOICE] -> Ý định dự đoán: {prediction} (Độ tin cậy: {confidence*100:.1f}%)")
                
                # prediction có dạng "device:action", ví dụ "led:on"
                if ":" in prediction:
                    device, action = prediction.split(":")
                    self._publish_command(device, action)
            else:
                logger.info(f"[VOICE] Không chắc chắn về ý định (Độ tin cậy: {confidence*100:.1f}% < 40%)")
                
        except Exception as e:
            logger.error(f"[VOICE] Lỗi khi dự đoán ý định: {e}")
            logger.debug(traceback.format_exc())

    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback của PyAudio để đọc mic liên tục và không block thread chính"""
        self.q.put(in_data)
        return (None, pyaudio.paContinue)

    def _listen_loop(self):
        """Vòng lặp thu âm và nhận diện giọng nói"""
        if not self.vosk_model:
            logger.error("[VOICE] Vosk model chưa được khởi tạo. Voice Recognition sẽ dừng.")
            return

        rec = KaldiRecognizer(self.vosk_model, self.RATE)
        p = pyaudio.PyAudio()

        try:
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK,
                            stream_callback=self.audio_callback)
            
            stream.start_stream()
            logger.info("[VOICE] Đang lắng nghe microphone...")

            while self.running:
                try:
                    # Chờ lấy dữ liệu từ queue (timeout 0.1s để vòng lặp có thể thoát)
                    data = self.q.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Đưa audio data vào Vosk
                if rec.AcceptWaveform(data):
                    # Lấy kết quả văn bản khi người dùng nói xong 1 câu
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        self._process_text(text)
                else:
                    # Có thể đọc kết quả từng phần (partial result) nếu muốn UI hiển thị realtime
                    # partial_result = json.loads(rec.PartialResult())
                    pass

        except Exception as e:
            logger.error(f"[VOICE] Lỗi trong lúc thu âm: {e}")
            logger.debug(traceback.format_exc())
        finally:
            logger.info("[VOICE] Đóng microphone...")
            try:
                if 'stream' in locals() and stream.is_active():
                    stream.stop_stream()
                    stream.close()
                p.terminate()
            except Exception:
                pass

    def start(self):
        """Bắt đầu chạy nhận diện giọng nói trên background thread"""
        if self.running:
            return
            
        if not self.vosk_model or not self.intent_model:
            logger.warning("Voice models missing. VoiceController will not start.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True, name="VoiceThread")
        self.thread.start()
        logger.info("✓ Voice Controller thread started")

    def stop(self):
        """Dừng nhận diện giọng nói"""
        if not self.running:
            return
            
        logger.info("Stopping Voice Controller...")
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=2)
