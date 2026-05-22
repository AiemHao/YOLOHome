"""
Smart Curtain Control System
============================
AI model to control curtain open/close based on sensor inputs.

Sensors:
  - sunlight_percent: 0-100 (light sensor)
  - temperature: -10 to 50 (°C)
  - humidity_percent: 0-100 (%)

Output:
  - action: 0 (close curtain) or 1 (open curtain)

Workflow:
  1. Define control rules (with detailed comments)
  2. Generate synthetic training data (10k samples) based on rules
  3. Train Decision Tree model
  4. Test accuracy on test set (2k samples)
"""

import csv
import os
import pickle
import numpy as np
import uuid
from datetime import datetime, timedelta
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# ============================================================================
# SECTION 1: CONTROL RULES (Chi tiết các luật điều khiển rèm)
# ============================================================================

"""
LUẬT ĐIỀU KHIỂN RÈM (Curtain Control Rules):
==============================================

Mục tiêu: Tối ưu hóa ánh sáng tự nhiên, duy trì nhiệt độ và độ ẩm phù hợp.

RULE 1: Ánh sáng quá mạnh → Đóng rèm (action = 0)
--------
Khi: sunlight_percent > 70
Lý do: 
  - Ánh sáng quá mạnh gây chói mắt, ảnh hưởng đến công việc
  - Tránh tia UV làm hư hại nội thất
  - Giảm nhiệt độ trong phòng (tiết kiệm điện máy lạnh)

RULE 2: Ánh sáng yếu + Nhiệt độ thích hợp → Mở rèm (action = 1)
--------
Khi: sunlight_percent < 40 AND temperature < 28
Lý do:
  - Tận dụng ánh sáng tự nhiên tiết kiệm điện
  - Không quá nóng nên không cần che phủ

RULE 3: Nhiệt độ quá cao + Ánh sáng cao → Đóng rèm (action = 0)
--------
Khi: temperature > 32 AND sunlight_percent > 50
Lý do:
  - Giảm lượng nhiệt từ ánh nắng vào phòng
  - Giảm phụ tải máy lạnh, tiết kiệm năng lượng
  - Duy trì nhiệt độ thoải mái

RULE 4: Độ ẩm cao + Cần thoáng khí → Mở rèm (action = 1)
--------
Khi: humidity_percent > 75 AND sunlight_percent < 60
Lý do:
  - Cho phép không khí thoáng để giảm độ ẩm
  - Tránh mốc nấm, bốc mùi hôi
  - Không quá sáng nên không gây chói

RULE 5: Độ ẩm thấp + Ánh sáng vừa phải → Mở rèm (action = 1)
--------
Khi: humidity_percent < 50 AND 30 < sunlight_percent < 70
Lý do:
  - Độ ẩm tốt (không cần thoáng)
  - Ánh sáng vừa phải tận dụng ánh sáng tự nhiên
  - Duy trì điều kiện sáng sao thoải mái

RULE 6: Nhiệt độ thấp + Ánh sáng cao → Mở rèm (action = 1)
--------
Khi: temperature < 15 AND sunlight_percent > 50
Lý do:
  - Trời lạnh, cần tận dụng nhiệt từ ánh nắng
  - Tiết kiệm điện sưởi ấm
  - Ánh sáng cao không gây chối khi nhiệt độ thấp

RULE 7: Cân bằng (Neutral) → Mở rèm (action = 1)
--------
Khi: Các điều kiện khác
Lý do:
  - Mở rèm là trạng thái mặc định
  - Cho phép ánh sáng tự nhiên
  - Tiết kiệm điện

LƯU Ý: Các luật được sắp xếp theo độ ưu tiên từ cao xuống thấp
"""


class CurtainControlRules:
    """
    Thực hiện các luật điều khiển rèm dựa trên input sensor.
    """
    
    @staticmethod
    def apply_rules(sunlight, temperature, humidity):
        """
        Áp dụng các luật để xác định hành động.
        
        Args:
            sunlight (float): 0-100, phần trăm ánh sáng
            temperature (float): Nhiệt độ (°C)
            humidity (int): 0-100, phần trăm độ ẩm
        
        Returns:
            int: 0 (đóng rèm) hoặc 1 (mở rèm)
        """
        
        # RULE 1: Ánh sáng quá mạnh → Đóng rèm
        if sunlight > 90:
            return 0  # Đóng rèm
        
        # RULE 3: Nhiệt độ quá cao + Ánh sáng cao → Đóng rèm
        if temperature >= 33 and sunlight > 70:
            return 0  # Đóng rèm
        
        # RULE 2: Ánh sáng yếu + Nhiệt độ thích hợp → Mở rèm
        if sunlight < 40 and temperature < 33:
            return 1  # Mở rèm
        
        # RULE 4: Độ ẩm cao + Cần thoáng khí → Mở rèm
        if humidity > 75 and sunlight < 60:
            return 1  # Mở rèm
        
        # RULE 5: Độ ẩm thấp + Ánh sáng vừa phải → Mở rèm
        if humidity < 50 and 30 <= sunlight <= 70:
            return 1  # Mở rèm
        
        # RULE 6: Nhiệt độ thấp + Ánh sáng cao → Mở rèm
        if temperature < 15 and sunlight > 50:
            return 1  # Mở rèm
        
        # RULE 7: Cân bằng (Neutral) → Mở rèm
        return 1  # Mở rèm (trạng thái mặc định)


# ============================================================================
# SECTION 2: DATA GENERATOR (Sinh dữ liệu theo các luật)
# ============================================================================

class CurtainDataGenerator:
    """
    Sinh dữ liệu huấn luyện dựa trên các luật điều khiển rèm.
    """
    
    def __init__(self, seed=42):
        """
        Khởi tạo generator.
        
        Args:
            seed (int): Random seed để tái lập dữ liệu
        """
        np.random.seed(seed)
        self.rules = CurtainControlRules()
        
    def generate_sensor_values(self):
        """
        Sinh giá trị cảm biến một cách ngẫu nhiên nhưng thực tế.
        
        Returns:
            tuple: (sunlight, temperature, humidity)
        """
        # Sinh giá trị ánh sáng (0-100) với phân bố Gaussian
        sunlight = np.clip(np.random.normal(50, 25), 0, 100)
        
        # Sinh giá trị nhiệt độ (-10 đến 50°C)
        temperature = np.random.uniform(-10, 50)
        
        # Sinh giá trị độ ẩm (0-100%) với phân bố Gaussian
        humidity = np.clip(np.random.normal(60, 20), 0, 100)
        
        return sunlight, temperature, humidity
    
    def generate_dataset(self, n_samples, output_file):
        """
        Sinh n_samples mẫu dữ liệu và lưu vào file CSV.
        
        Args:
            n_samples (int): Số lượng mẫu cần sinh
            output_file (str): Đường dẫn file output CSV
        """
        print(f"Generating {n_samples} samples to {output_file}...")
        
        fieldnames = [
            "event_id", "timestamp", 
            "sunlight_percent", "temperature", "humidity_percent",
            "action"
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            base_time = datetime.now()
            
            for i in range(n_samples):
                # Sinh sensor values
                sunlight, temperature, humidity = self.generate_sensor_values()
                
                # Áp dụng luật để xác định action
                action = self.rules.apply_rules(sunlight, temperature, humidity)
                
                # Ghi dữ liệu
                writer.writerow({
                    "event_id": str(uuid.uuid4())[:8],
                    "timestamp": int((base_time + timedelta(minutes=i)).timestamp()),
                    "sunlight_percent": round(sunlight, 2),
                    "temperature": round(temperature, 2),
                    "humidity_percent": round(humidity, 2),
                    "action": action
                })
                
                # Progress log
                if (i + 1) % 1000 == 0:
                    print(f"  Generated {i + 1}/{n_samples} samples...")
        
        print(f"✓ Data saved to {output_file}")


# ============================================================================
# SECTION 3: TRAIN MODEL (Huấn luyện Decision Tree)
# ============================================================================

class CurtainModelTrainer:
    """
    Huấn luyện Decision Tree model để điều khiển rèm.
    """
    
    def __init__(self):
        self.model = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42
        )
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
    
    def load_data(self, csv_file):
        """
        Tải dữ liệu từ file CSV.
        
        Args:
            csv_file (str): Đường dẫn file CSV
        
        Returns:
            tuple: (X, y) - features và labels
        """
        print(f"Loading data from {csv_file}...")
        
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        print(f"  Loaded {len(data)} samples")
        
        # Trích xuất features (X) và label (y)
        X = np.array([
            [
                float(row['sunlight_percent']),
                float(row['temperature']),
                float(row['humidity_percent'])
            ]
            for row in data
        ])
        
        y = np.array([int(row['action']) for row in data])
        
        return X, y
    
    def train(self, train_file):
        """
        Huấn luyện model trên dữ liệu training.
        
        Args:
            train_file (str): Đường dẫn file training data
        """
        print("Training model...")
        
        # Load data
        X, y = self.load_data(train_file)
        
        # Chia thành train/test (từ train_file)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"  Train set: {len(self.X_train)} samples")
        print(f"  Validation set: {len(self.X_test)} samples")
        
        # Huấn luyện model
        self.model.fit(self.X_train, self.y_train)
        
        print("✓ Model trained successfully!")
    
    def evaluate(self):
        """
        Đánh giá model trên tập validation.
        """
        print("\nEvaluating model on validation set...")
        
        y_pred = self.model.predict(self.X_test)
        accuracy = accuracy_score(self.y_test, y_pred)
        
        print(f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
        print("\nClassification Report:")
        print(classification_report(self.y_test, y_pred, 
              target_names=['Close (0)', 'Open (1)']))
        
        # Confusion Matrix
        cm = confusion_matrix(self.y_test, y_pred)
        print("\nConfusion Matrix:")
        print(f"                Predicted 0  Predicted 1")
        print(f"Actual 0         {cm[0][0]:>5}        {cm[0][1]:>5}")
        print(f"Actual 1         {cm[1][0]:>5}        {cm[1][1]:>5}")
        
        return accuracy
    
    def test_on_external_set(self, test_file):
        """
        Kiểm thử model trên test set độc lập.
        
        Args:
            test_file (str): Đường dẫn file test data
        """
        print(f"\nTesting on external test set ({test_file})...")
        
        X_test, y_test = self.load_data(test_file)
        
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Test Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, 
              target_names=['Close (0)', 'Open (1)']))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print("\nConfusion Matrix:")
        print(f"                Predicted 0  Predicted 1")
        print(f"Actual 0         {cm[0][0]:>5}        {cm[0][1]:>5}")
        print(f"Actual 1         {cm[1][0]:>5}        {cm[1][1]:>5}")
        
        return accuracy
    
    def predict(self, sunlight, temperature, humidity):
        """
        Dự đoán hành động dựa trên input sensor.
        
        Args:
            sunlight (float): 0-100
            temperature (float): Nhiệt độ (°C)
            humidity (float): 0-100
        
        Returns:
            int: 0 (đóng) hoặc 1 (mở)
        """
        X = np.array([[sunlight, temperature, humidity]])
        return self.model.predict(X)[0]


# ============================================================================
# SECTION 4: TEST & DEMO
# ============================================================================

def main():
    """
    Main workflow: generate data, train model, test.
    """
    
    print("=" * 80)
    print("SMART CURTAIN CONTROL SYSTEM")
    print("=" * 80)
    
    # Create output directory
    os.makedirs("data", exist_ok=True)
    
    # Step 1: Generate training data (10k samples)
    print("\n[STEP 1] Generating training data (10,000 samples)...")
    generator = CurtainDataGenerator(seed=42)
    train_file = "data/curtain_train.csv"
    generator.generate_dataset(n_samples=10000, output_file=train_file)
    
    # Step 2: Generate test data (2k samples)
    print("\n[STEP 2] Generating test data (2,000 samples)...")
    test_file = "data/curtain_test.csv"
    generator.generate_dataset(n_samples=2000, output_file=test_file)
    
    # Step 3: Train model
    print("\n[STEP 3] Training Decision Tree model...")
    trainer = CurtainModelTrainer()
    trainer.train(train_file)
    
    # Step 4: Evaluate on internal validation set
    print("\n[STEP 4] Evaluating on internal validation set (20% of training data)...")
    train_accuracy = trainer.evaluate()
    
    # Step 5: Test on external test set
    print("\n[STEP 5] Testing on external test set (2,000 samples)...")
    test_accuracy = trainer.test_on_external_set(test_file)
    
    # Step 6: Demo predictions
    print("\n[STEP 6] Demo predictions on sample inputs:")
    print("-" * 80)
    
    test_cases = [
        {"sunlight": 80, "temperature": 35, "humidity": 50, "desc": "Bright & hot"},
        {"sunlight": 20, "temperature": 25, "humidity": 60, "desc": "Dark & mild"},
        {"sunlight": 50, "temperature": 10, "humidity": 40, "desc": "Moderate & cold"},
        {"sunlight": 30, "temperature": 25, "humidity": 80, "desc": "Dim & humid"},
        {"sunlight": 90, "temperature": 15, "humidity": 30, "desc": "Very bright & cool"},
    ]
    
    for tc in test_cases:
        sunlight = tc["sunlight"]
        temperature = tc["temperature"]
        humidity = tc["humidity"]
        
        # Dự đoán từ model
        model_action = trainer.predict(sunlight, temperature, humidity)
        model_result = "OPEN" if model_action == 1 else "CLOSE"
        
        # Dự đoán từ luật
        rule_action = CurtainControlRules.apply_rules(sunlight, temperature, humidity)
        rule_result = "OPEN" if rule_action == 1 else "CLOSE"
        
        match = "✓" if model_action == rule_action else "✗"
        
        print(f"{match} {tc['desc']:20} | "
              f"L={sunlight:5.1f} T={temperature:5.1f} H={humidity:5.1f} | "
              f"Rules: {rule_result:5} | Model: {model_result:5}")
    
    print("-" * 80)
    print(f"\nTraining Accuracy: {train_accuracy * 100:.2f}%")
    print(f"Test Accuracy:     {test_accuracy * 100:.2f}%")
    print("\n✓ System ready! Model can now be used for curtain control.")
    
    # Save the trained model
    print("\n[STEP 7] Saving trained model...")
    model_dir = "models"
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
    
    model_file = os.path.join(model_dir, "curtain_model.pkl")
    with open(model_file, 'wb') as f:
        pickle.dump(trainer.model, f)
    print(f"✓ Model saved to: {model_file}")


if __name__ == "__main__":
    main()
