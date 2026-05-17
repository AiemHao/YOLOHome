import axios from 'axios';
import FormData from 'form-data';
import dotenv from 'dotenv';
dotenv.config();

const VOSK_URL = process.env.VOSK_SERVER_URL || 'http://localhost:8500/transcribe';

export default async function transcribeWithVosk(audioBuffer) {
  const form = new FormData();
  form.append('file', audioBuffer, { filename: 'audio.wav', contentType: 'audio/wav' });
  const resp = await axios.post(VOSK_URL, form, { headers: form.getHeaders() });
  return resp.data.transcript || '';
}
