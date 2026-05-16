import sys
sys.path.insert(0, 'YOLOHome-Gateway/GateWay')
from Controller.services import AIService
from pathlib import Path

# Test model loading
model_path = Path('YOLOHome-Gateway/GateWay/Decision_tree/models/curtain_model.pkl')
ai_service = AIService(model_path=str(model_path), enabled=True)

print(f'AI Service Status:')
print(f'  Model Loaded: {ai_service.is_enabled()}')
print(f'  Model Info: {ai_service.get_model_info()}')

# Test prediction with sample data
sensor_data = {
    'light': 50.0,
    'temp': 25.0,
    'humi': 60.0
}

prediction = ai_service.predict_action(sensor_data)
action = 'OPEN' if prediction == 1 else 'CLOSE'
print(f'\nSample Prediction (L=50, T=25, H=60): {prediction} ({action})')
