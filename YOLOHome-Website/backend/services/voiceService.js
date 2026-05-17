import transcribe from '../utils/sttProvider.js';
import axios from 'axios';
import { mqttClientService } from './mqtt/mqttClientService.js';
import ControlTrace from '../models/ControlTrace.js';

export async function handleVoiceCommand(file) {
  let traceData = {
    source: 'frontend', // or voice-api
    action: 'voice_command',
    status: 'success'
  };

  try {
    const audioBuffer = file.buffer;
    const transcript = await transcribe(audioBuffer);
    
    if (!transcript || transcript.trim() === '') {
      throw new Error('No speech recognized');
    }

    // Call ML micro-service
    const mlUrl = process.env.ML_SERVICE_URL || 'http://localhost:8000/predict';
    const mlResp = await axios.post(mlUrl, { text: transcript });
    const intent = mlResp.data.intent; // {action, device, ...}
    
    if (!intent || !intent.action) throw new Error('Intent not recognized');
    
    traceData.action = `voice_${intent.action}_${intent.device || 'unknown'}`;
    traceData.payload = { text: transcript, intent };

    const location = intent.location || 'default';
    const device = intent.device;
    if (!device) throw new Error('Device not specified in intent');

    const topic = `home/${location}/device/${device}/set`;
    const mqttPayload = { action: intent.action };
    
    traceData.mqttTopic = topic;
    traceData.mqttPayload = mqttPayload;
    
    if (mqttClientService) {
        await mqttClientService.publish(topic, mqttPayload);
    } else {
        console.warn('MQTT client not connected, skipping publish to', topic);
        throw new Error('MQTT client not connected');
    }
    
    // Fire & forget log
    ControlTrace.create(traceData).catch(err => console.error('[Log Error]', err));

    return { transcript, intent };
  } catch (error) {
    traceData.status = 'failure';
    traceData.errorMsg = error.message;
    // Fire & forget log
    ControlTrace.create(traceData).catch(err => console.error('[Log Error]', err));
    throw error;
  }
}
