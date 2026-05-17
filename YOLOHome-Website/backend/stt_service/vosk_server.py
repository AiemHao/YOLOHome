import os, wave, json
from fastapi import FastAPI, HTTPException, UploadFile, File
from vosk import Model, KaldiRecognizer

app = FastAPI()
MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-vi")
if not os.path.isdir(MODEL_PATH):
    raise RuntimeError(f"Vosk model folder not found at {MODEL_PATH}")
model = Model(MODEL_PATH)

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        wf = wave.open(file.file, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() not in (8000, 16000):
            raise HTTPException(status_code=400, detail="Audio must be mono PCM 16-bit, 8kHz or 16kHz")
        rec = KaldiRecognizer(model, wf.getframerate())
        result = ""
        while True:
            data = wf.readframes(4000)
            if not data:
                break
            if rec.AcceptWaveform(data):
                result += json.loads(rec.Result())["text"] + " "
        result += json.loads(rec.FinalResult())["text"]
        return {"transcript": result.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
