import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib

app = FastAPI()

class PredictRequest(BaseModel):
    text: str

# Load the previously trained model
MODEL_PATH = os.getenv("MODEL_PATH", r"..\..\..\YOLOHome-Gateway\GateWay\Voice\models\intent_model.pkl")
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file not found at {MODEL_PATH}")
model = joblib.load(MODEL_PATH)

def preprocess(txt: str):
    return txt.lower().strip()

@app.post("/predict")
def predict(req: PredictRequest):
    try:
        processed = preprocess(req.text)
        pred = model.predict([processed])[0]
        return {"intent": pred}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
