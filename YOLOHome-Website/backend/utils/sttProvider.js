import axios from 'axios';
import FormData from 'form-data';
import dotenv from 'dotenv';
dotenv.config();

import transcribeWithVosk from './voskProvider.js';

const sttProvider = (process.env.STT_PROVIDER || 'whisper').toLowerCase();
const whisperKey = process.env.WHISPER_API_KEY;
const googleKey = process.env.GOOGLE_STT_API_KEY;

const transcribeWithWhisper = async (audioBuffer) => {
  const form = new FormData();
  form.append('file', audioBuffer, { filename: 'audio.webm', contentType: 'audio/webm' });
  form.append('model', 'whisper-1');
  const resp = await axios.post('https://api.openai.com/v1/audio/transcriptions', form, {
    headers: {
      'Authorization': `Bearer ${whisperKey}`,
      ...form.getHeaders()
    }
  });
  return resp.data.text;
};

const transcribeWithGoogle = async (audioBuffer) => {
  const resp = await axios.post('https://speech.googleapis.com/v1/speech:recognize?key=' + googleKey, {
    config: {
      encoding: 'WEBM_OPUS', // adjust based on front-end output
      languageCode: 'vi-VN',
    },
    audio: { content: audioBuffer.toString('base64') },
  });
  return resp.data.results?.[0]?.alternatives?.[0]?.transcript || '';
};

export default async function transcribe(audioBuffer) {
  switch (sttProvider) {
    case 'whisper': return await transcribeWithWhisper(audioBuffer);
    case 'google':  return await transcribeWithGoogle(audioBuffer);
    case 'vosk':    return await transcribeWithVosk(audioBuffer);
    default: throw new Error(`Unsupported STT provider: ${sttProvider}`);
  }
}
