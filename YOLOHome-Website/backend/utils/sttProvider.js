import dotenv from 'dotenv';
dotenv.config();

import transcribeWithVosk from './voskProvider.js';

export default async function transcribe(audioBuffer) {
  return await transcribeWithVosk(audioBuffer);
}
