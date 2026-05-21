import mqttConfig from '../../config/mqtt.js';
import { SensorService } from '../sensorService.js';
import { DeviceService } from '../deviceService.js';
import { alertService } from '../alertService.js';
import { mqttClientService } from './mqttClientService.js';
import {
    MQTT_DEVICE_TOPICS,
    MQTT_SENSOR_TOPICS,
    MQTT_SUBSCRIBE_TOPICS,
    MQTT_SYSTEM_ACTIONS,
    MQTT_SYSTEM_TOPICS,
    matchDeviceStateTopic,
    matchSensorTopic,
    matchSystemTopic
} from './mqttTopics.js';

const SENSOR_NAME_MAP = {
    temp: 'temperature',
    temperature: 'temperature',
    humi: 'humidity',
    humidity: 'humidity',
    light: 'light'
};

const DEVICE_NAME_MAP = {
    led: 'Led',
    light: 'Led',
    fan: 'Fan',
    servo: 'Servo'
};

const DEVICE_TYPE_BY_NAME = {
    Led: 'led',
    Fan: 'fan',
    Servo: 'servo'
};

const DEVICE_FIELD_MAP = {
    Led: 'light',
    Fan: 'fan',
    Servo: 'servo'
};

const pendingResponses = new Map();
const SYSTEM_STATEALL_RESPONSE_KEY = `system:${MQTT_SYSTEM_ACTIONS.STATE_ALL}`;
const MQTT_ALLOWED_SYSTEM_ACTIONS = new Set([MQTT_SYSTEM_ACTIONS.GET_ALL]);
const sensorSnapshotBuffer = {
    temperature: null,
    humidity: null,
    light: null
};
const deviceSnapshotBuffer = {
    light: null,
    fan: null,
    servo: null
};

const normalizeSensorType = (rawType) => {
    if (!rawType) {
        return null;
    }
    return SENSOR_NAME_MAP[String(rawType).trim().toLowerCase()] || null;
};

const normalizeDeviceName = (rawName) => {
    if (!rawName) {
        return null;
    }
    return DEVICE_NAME_MAP[String(rawName).trim().toLowerCase()] || null;
};

const waitForResponse = (responseKey, timeoutMs = mqttConfig.responseTimeoutMs) => {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            pendingResponses.delete(responseKey);
            reject(new Error(`MQTT response timeout for key=${responseKey}`));
        }, timeoutMs);

        pendingResponses.set(responseKey, {
            resolve,
            timeout
        });
    });
};

const resolveResponse = (responseKey, payload) => {
    const pending = pendingResponses.get(responseKey);
    if (!pending) {
        return false;
    }

    clearTimeout(pending.timeout);
    pendingResponses.delete(responseKey);
    pending.resolve(payload);
    return true;
};

const clearResponses = () => {
    for (const pending of pendingResponses.values()) {
        clearTimeout(pending.timeout);
    }
    pendingResponses.clear();
};

const logMqtt = (message, meta = {}) => {
    console.log(`[MQTT] ${message}`, meta);
};

const handleDeviceState = async (payload, topicParams) => {
    const deviceName = normalizeDeviceName(payload?.device || payload?.deviceType || topicParams.type);
    const rawStatus = payload?.action ?? payload?.status;
    const status = rawStatus === 'on' || rawStatus === 'off' ? rawStatus : null;

    logMqtt('Device state message received', {
        room: topicParams.room,
        type: topicParams.type,
        rawStatus
    });

    if (deviceName && status) {
        const field = DEVICE_FIELD_MAP[deviceName];
        if (!field) {
            return;
        }

        deviceSnapshotBuffer[field] = status;
        const latestSnapshot = await DeviceService.getLatestSnapshot();

        const mergedSnapshot = {
            light: latestSnapshot?.light ?? deviceSnapshotBuffer.light,
            fan: latestSnapshot?.fan ?? deviceSnapshotBuffer.fan,
            servo: latestSnapshot?.servo ?? deviceSnapshotBuffer.servo,
            timestamp: payload?.timestamp ? new Date(payload.timestamp) : new Date()
        };

        mergedSnapshot[field] = status;

        await DeviceService.saveDeviceSnapshot(mergedSnapshot);

        logMqtt('Device snapshot saved to database', {
            light: mergedSnapshot.light,
            fan: mergedSnapshot.fan,
            servo: mergedSnapshot.servo
        });

        deviceSnapshotBuffer.light = null;
        deviceSnapshotBuffer.fan = null;
        deviceSnapshotBuffer.servo = null;
    }
};

const handleSensorTelemetry = async (payload, topicParams) => {
    const sensorType = normalizeSensorType(payload?.sensorType || topicParams.type);
    const value = Number(payload?.value);

    logMqtt('Sensor telemetry message received', {
        room: topicParams.room,
        type: topicParams.type,
        value: payload?.value
    });

    if (!sensorType || Number.isNaN(value)) {
        console.warn('MQTT sensor payload dropped: invalid payload', payload);
        return;
    }

    sensorSnapshotBuffer[sensorType] = value;

    const hasFullSnapshot =
        sensorSnapshotBuffer.temperature !== null &&
        sensorSnapshotBuffer.humidity !== null &&
        sensorSnapshotBuffer.light !== null;

    if (!hasFullSnapshot) {
        return;
    }

    await SensorService.saveSensorSnapshot({
        temperature: sensorSnapshotBuffer.temperature,
        humidity: sensorSnapshotBuffer.humidity,
        light: sensorSnapshotBuffer.light,
        timestamp: payload?.timestamp ? new Date(payload.timestamp) : new Date()
    });

    // Check thresholds and generate alerts
    await alertService.checkAndAlert('temperature', sensorSnapshotBuffer.temperature);
    await alertService.checkAndAlert('humidity', sensorSnapshotBuffer.humidity);
    await alertService.checkAndAlert('light', sensorSnapshotBuffer.light);

    logMqtt('Sensor snapshot saved to database', {
        temperature: sensorSnapshotBuffer.temperature,
        humidity: sensorSnapshotBuffer.humidity,
        light: sensorSnapshotBuffer.light
    });

    sensorSnapshotBuffer.temperature = null;
    sensorSnapshotBuffer.humidity = null;
    sensorSnapshotBuffer.light = null;
};

const handleSystemSnapshot = async (payload) => {
    const temperature = Number(payload?.temp);
    const humidity = Number(payload?.humi);
    const light = Number(payload?.light);

    logMqtt('System snapshot message received', {
        temp: payload?.temp,
        humi: payload?.humi,
        light: payload?.light,
        led: payload?.led,
        fan: payload?.fan,
        servo: payload?.servo
    });

    if (!Number.isNaN(temperature) && !Number.isNaN(humidity) && !Number.isNaN(light)) {
        await SensorService.saveSensorSnapshot({
            temperature,
            humidity,
            light,
            timestamp: new Date()
        });

        logMqtt('System snapshot sensor data saved to database', {
            temperature,
            humidity,
            light
        });
    }

    const lightStatus = payload?.led;
    const fanStatus = payload?.fan;
    const servoStatus = payload?.servo;

    if (
        (lightStatus === 'on' || lightStatus === 'off') &&
        (fanStatus === 'on' || fanStatus === 'off') &&
        (servoStatus === 'on' || servoStatus === 'off')
    ) {
        await DeviceService.saveDeviceSnapshot({
            light: lightStatus,
            fan: fanStatus,
            servo: servoStatus,
            timestamp: new Date()
        });

        logMqtt('System snapshot device data saved to database', {
            light: lightStatus,
            fan: fanStatus,
            servo: servoStatus
        });
    }
};

const routeMessage = async (topic, payload) => {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
        console.warn('MQTT payload dropped: payload must be a JSON object', { topic, payload });
        return;
    }

    const deviceStateParams = matchDeviceStateTopic(topic);
    if (deviceStateParams) {
        await handleDeviceState(payload, deviceStateParams);
        return;
    }

    const sensorParams = matchSensorTopic(topic);
    if (sensorParams) {
        await handleSensorTelemetry(payload, sensorParams);
        return;
    }

    const systemParams = matchSystemTopic(topic);
    if (systemParams) {
        if (systemParams.action === MQTT_SYSTEM_ACTIONS.STATE_ALL) {
            await handleSystemSnapshot(payload);
            resolveResponse(SYSTEM_STATEALL_RESPONSE_KEY, payload);
            return;
        }

        console.log(`MQTT system message received: action=${systemParams.action}`);
    }
};

const start = async () => {
    if (!mqttConfig.enabled) {
        console.log('MQTT disabled by configuration');
        return;
    }

    await mqttClientService.start();
    await mqttClientService.subscribe(MQTT_SUBSCRIBE_TOPICS);

    mqttClientService.onMessage(async (topic, payload) => {
        try {
            await routeMessage(topic, payload);
        } catch (error) {
            console.error('MQTT message route error:', error.message);
        }
    });

    console.log('MQTT subscriptions ready');
};

const stop = async () => {
    clearResponses();
    await mqttClientService.stop();
};

const sendDeviceCommand = async ({ deviceType, deviceName, action, status }) => {
    const normalizedDeviceName = normalizeDeviceName(deviceType || deviceName);
    const resolvedDeviceType = normalizedDeviceName ? DEVICE_TYPE_BY_NAME[normalizedDeviceName] : null;
    const gatewayAction = action ?? status;

    if (gatewayAction !== 'on' && gatewayAction !== 'off') {
        throw new Error('Invalid device action: must be exactly "on" or "off"');
    }

    if (!resolvedDeviceType) {
        throw new Error('Invalid device identifier: use led, fan, or servo');
    }

    if (!mqttConfig.enabled) {
        return {
            published: false,
            skipped: true
        };
    }

    const topic = MQTT_DEVICE_TOPICS.buildCommand(resolvedDeviceType);
    const mqttPayload = { action: gatewayAction };
    await mqttClientService.publish(topic, mqttPayload);

    return {
        published: true,
        deviceType: resolvedDeviceType,
        topic,
        mqttPayload
    };
};

const sendSystemAction = async ({ action, payload = {} }) => {
    if (!MQTT_ALLOWED_SYSTEM_ACTIONS.has(action)) {
        throw new Error(`Unsupported MQTT system action: ${action}`);
    }

    if (!mqttConfig.enabled) {
        return {
            published: false,
            skipped: true
        };
    }

    const topic = MQTT_SYSTEM_TOPICS.buildAction(action);
    const responsePromise = waitForResponse(SYSTEM_STATEALL_RESPONSE_KEY);

    await mqttClientService.publish(topic, payload);

    return {
        published: true,
        response: await responsePromise
    };
};

const sendGetAll = async () => {
    return sendSystemAction({
        action: MQTT_SYSTEM_ACTIONS.GET_ALL
    });
};

export const mqttService = {
    start,
    stop,
    sendDeviceCommand,
    sendGetAll
};
