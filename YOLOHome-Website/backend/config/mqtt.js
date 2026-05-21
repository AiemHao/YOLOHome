const mqttConfig = {
    enabled: process.env.MQTT_ENABLED !== 'false',
    brokerUrl: process.env.MQTT_BROKER_URL || 'mqtt://localhost:1883',
    username: process.env.MQTT_USERNAME || '',
    password: process.env.MQTT_PASSWORD || '',
    clientId: process.env.MQTT_CLIENT_ID || `yolohome-backend-${Math.random().toString(16).slice(2, 10)}`,
    qos: Number(process.env.MQTT_QOS || 1),
    retain: process.env.MQTT_RETAIN === 'true',
    responseTimeoutMs: 5000,
    topicPrefix: process.env.MQTT_TOPIC_PREFIX || 'home',
    location: process.env.MQTT_LOCATION || 'livingroom'
};

export default mqttConfig;
