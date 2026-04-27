import mqtt from 'mqtt';
import mqttConfig from '../../config/mqtt.js';

class MqttClientService {
    constructor() {
        this.client = null;
        this.started = false;
        this.messageHandlers = [];
    }

    async start() {
        if (!mqttConfig.enabled || this.started) {
            return;
        }

        const options = {
            clientId: mqttConfig.clientId,
            username: mqttConfig.username || undefined,
            password: mqttConfig.password || undefined,
            reconnectPeriod: 2000,
            clean: true
        };

        this.client = mqtt.connect(mqttConfig.brokerUrl, options);

        await new Promise((resolve, reject) => {
            this.client.once('connect', () => {
                this.started = true;
                console.log(`MQTT connected: ${mqttConfig.brokerUrl}`);
                resolve();
            });

            this.client.once('error', (error) => {
                reject(error);
            });
        });

        this.client.on('reconnect', () => {
            console.log('MQTT reconnecting...');
        });

        this.client.on('error', (error) => {
            console.error('MQTT client error:', error.message);
        });

        this.client.on('message', (topic, buffer) => {
            const raw = buffer.toString();
            let payload = raw;
            try {
                payload = JSON.parse(raw);
            } catch (error) {
                payload = raw;
            }

            for (const handler of this.messageHandlers) {
                handler(topic, payload);
            }
        });
    }

    async subscribe(topics) {
        if (!this.client || !this.started) {
            throw new Error('MQTT client is not started');
        }

        const topicList = Array.isArray(topics) ? topics : [topics];
        await new Promise((resolve, reject) => {
            this.client.subscribe(topicList, { qos: mqttConfig.qos }, (error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    }

    async publish(topic, payload, options = {}) {
        if (!this.client || !this.started) {
            throw new Error('MQTT client is not started');
        }

        const message = typeof payload === 'string' ? payload : JSON.stringify(payload);
        const publishOptions = {
            qos: mqttConfig.qos,
            retain: mqttConfig.retain,
            ...options
        };

        await new Promise((resolve, reject) => {
            this.client.publish(topic, message, publishOptions, (error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    async stop() {
        if (!this.client) {
            return;
        }

        await new Promise((resolve) => {
            this.client.end(false, {}, () => {
                resolve();
            });
        });

        this.started = false;
        this.client = null;
        this.messageHandlers = [];
        console.log('MQTT disconnected');
    }
}

export const mqttClientService = new MqttClientService();
