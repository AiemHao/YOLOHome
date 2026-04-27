const MQTT_PREFIX = 'home';
const MQTT_LOCATION = 'livingroom';

export const MQTT_SYSTEM_ACTIONS = Object.freeze({
    GET_ALL: 'getall',
    STATE_ALL: 'stateall'
});

export const MQTT_DEVICE_TOPICS = Object.freeze({
    buildCommand: (deviceType) => `${MQTT_PREFIX}/${MQTT_LOCATION}/device/${deviceType}/set`,
    buildState: (deviceType) => `${MQTT_PREFIX}/${MQTT_LOCATION}/device/${deviceType}/state`,
    subscribeState: `${MQTT_PREFIX}/+/device/+/state`
});

export const MQTT_SENSOR_TOPICS = Object.freeze({
    buildState: (sensorType) => `${MQTT_PREFIX}/${MQTT_LOCATION}/sensor/${sensorType}`,
    subscribeState: `${MQTT_PREFIX}/+/sensor/+`
});

export const MQTT_SYSTEM_TOPICS = Object.freeze({
    buildAction: (action) => `${MQTT_PREFIX}/system/${action}`,
    subscribeAll: `${MQTT_PREFIX}/system/+`
});

export const MQTT_SUBSCRIBE_TOPICS = Object.freeze([
    MQTT_DEVICE_TOPICS.subscribeState,
    MQTT_SENSOR_TOPICS.subscribeState,
    MQTT_SYSTEM_TOPICS.subscribeAll
]);

const splitTopic = (topic) => String(topic || '').split('/');

export const matchDeviceStateTopic = (topic) => {
    const parts = splitTopic(topic);
    if (parts.length !== 5) {
        return null;
    }
    const [prefix, room, kind, type, action] = parts;
    if (prefix !== MQTT_PREFIX || kind !== 'device' || action !== 'state') {
        return null;
    }
    return { room, type };
};

export const matchSensorTopic = (topic) => {
    const parts = splitTopic(topic);
    if (parts.length !== 4) {
        return null;
    }
    const [prefix, room, kind, type] = parts;
    if (prefix !== MQTT_PREFIX || kind !== 'sensor') {
        return null;
    }
    return { room, type };
};

export const matchSystemTopic = (topic) => {
    const parts = splitTopic(topic);
    if (parts.length !== 3) {
        return null;
    }
    const [prefix, section, action] = parts;
    if (prefix !== MQTT_PREFIX || section !== 'system') {
        return null;
    }
    return { action };
};
