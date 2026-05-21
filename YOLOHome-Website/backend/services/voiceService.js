import transcribe from '../utils/sttProvider.js';
import axios from 'axios';
import { mqttClientService } from './mqtt/mqttClientService.js';
import { MQTT_DEVICE_TOPICS } from './mqtt/mqttTopics.js';
import { mqttService } from './mqtt/mqttService.js';
import ControlTrace from '../models/ControlTrace.js';
import { DeviceService } from './deviceService.js';

const ACTION_ALIASES = {
  on: ['on', 'open', 'mo', 'bat', 'mo rem', 'mo rem cua', 'keo len', 'keo len rem', 'bat den', 'bat quat'],
  off: ['off', 'close', 'dong', 'tat', 'keo', 'keo rem', 'keo xuong', 'keo xuong rem', 'tat den', 'tat quat']
};

const DEVICE_ALIASES = {
  servo: ['servo', 'rem', 'rem cua', 'curtain'],
  led: ['led', 'den', 'light'],
  fan: ['fan', 'quat']
};

const DEVICE_FIELD_BY_TYPE = {
  led: 'light',
  light: 'light',
  fan: 'fan',
  servo: 'servo'
};

const normalizeText = (text) => {
  if (!text) {
    return '';
  }

  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
};

const normalizeAction = (rawAction) => {
  const normalized = normalizeText(rawAction);
  if (!normalized) {
    return null;
  }

  if (ACTION_ALIASES.on.some((alias) => normalized === alias)) {
    return 'on';
  }
  if (ACTION_ALIASES.off.some((alias) => normalized === alias)) {
    return 'off';
  }

  return normalized === 'on' || normalized === 'off' ? normalized : null;
};

const normalizeDevice = (rawDevice) => {
  const normalized = normalizeText(rawDevice);
  if (!normalized) {
    return null;
  }

  for (const [device, aliases] of Object.entries(DEVICE_ALIASES)) {
    if (aliases.some((alias) => normalized === alias)) {
      return device;
    }
  }

  return normalized;
};

const parseIntentFromText = (text) => {
  const normalized = normalizeText(text);
  if (!normalized) {
    return null;
  }

  let action = null;
  let device = null;

  for (const [candidateAction, aliases] of Object.entries(ACTION_ALIASES)) {
    if (aliases.some((alias) => normalized.includes(alias))) {
      action = candidateAction;
      break;
    }
  }

  for (const [candidateDevice, aliases] of Object.entries(DEVICE_ALIASES)) {
    if (aliases.some((alias) => normalized.includes(alias))) {
      device = candidateDevice;
      break;
    }
  }

  if (!action || !device) {
    return null;
  }

  return { device, action, raw: text, source: 'heuristic' };
};

const saveOptimisticSnapshot = async (device, action) => {
  const field = DEVICE_FIELD_BY_TYPE[device];
  if (!field || (action !== 'on' && action !== 'off')) {
    return;
  }

  const latestSnapshot = await DeviceService.getLatestSnapshot();
  await DeviceService.saveDeviceSnapshot({
    light: latestSnapshot?.light ?? null,
    fan: latestSnapshot?.fan ?? null,
    servo: latestSnapshot?.servo ?? null,
    [field]: action,
    timestamp: new Date()
  });
};

const normalizeIntent = (rawIntent, transcript) => {
  if (!rawIntent) {
    return parseIntentFromText(transcript);
  }

  if (typeof rawIntent === 'string') {
    const normalized = normalizeText(rawIntent);
    const parts = normalized.split(':').map((part) => part.trim()).filter(Boolean);

    if (parts.length === 2) {
      return {
        device: normalizeDevice(parts[0]),
        action: normalizeAction(parts[1]),
        raw: rawIntent
      };
    }

    const tokens = normalized.split(/[\s:_-]+/).filter(Boolean);
    const tokenDevice = tokens.find((token) => normalizeDevice(token));
    const tokenAction = tokens.find((token) => normalizeAction(token));

    if (tokenDevice && tokenAction) {
      return {
        device: normalizeDevice(tokenDevice),
        action: normalizeAction(tokenAction),
        raw: rawIntent
      };
    }

    return parseIntentFromText(transcript || rawIntent);
  }

  if (typeof rawIntent === 'object') {
    if (rawIntent.device && rawIntent.action) {
      return {
        ...rawIntent,
        device: normalizeDevice(rawIntent.device),
        action: normalizeAction(rawIntent.action)
      };
    }
  }

  return parseIntentFromText(transcript);
};

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
    const intent = normalizeIntent(mlResp.data.intent, transcript);

    if (!intent || !intent.action) throw new Error('Intent not recognized');
    
    traceData.action = `voice_${intent.action}_${intent.device || 'unknown'}`;
    traceData.payload = { text: transcript, intent };

    const device = intent.device;
    if (!device) throw new Error('Device not specified in intent');

    const topic = MQTT_DEVICE_TOPICS.buildCommand(device);
    const mqttPayload = { action: intent.action };
    
    traceData.mqttTopic = topic;
    traceData.mqttPayload = mqttPayload;
    
    if (mqttClientService) {
      await mqttClientService.publish(topic, mqttPayload);
      await saveOptimisticSnapshot(device, intent.action);
      try {
        await mqttService.sendGetAll();
      } catch (error) {
        console.warn('[VOICE] MQTT getall skipped:', error.message);
      }
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
