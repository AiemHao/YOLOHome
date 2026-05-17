import ThresholdTrace from '../models/ThresholdTrace.js';
import { mqttClientService } from './mqtt/mqttClientService.js';

// Dummy thresholds for demonstration (ideally should come from DB)
const THRESHOLDS = {
    temperature: { max: 35, thresholdId: 'temp_high', name: 'High Temperature' },
    humidity: { min: 30, thresholdId: 'hum_low', name: 'Low Humidity' },
    light: { min: 200, thresholdId: 'light_dark', name: 'Dark Environment' }
};

export const alertService = {
    processAlerts: async (topic, message) => {
        console.log('[Alert] Dummy processing for', topic);
    },
    checkAndAlert: async (sensorType, value) => {
        const threshold = THRESHOLDS[sensorType];
        if (!threshold) return;

        let triggered = false;
        let direction = '';

        if (threshold.max !== undefined && value > threshold.max) {
            triggered = true;
            direction = 'above';
        } else if (threshold.min !== undefined && value < threshold.min) {
            triggered = true;
            direction = 'below';
        }

        if (triggered) {
            console.log(`[Alert] ${threshold.name} triggered! Value: ${value}`);
            
            // Example system action: turn on a fan if temperature is high
            let actionTaken = 'log_only';
            let status = 'executed';
            let errorMsg = '';

            try {
                if (sensorType === 'temperature' && direction === 'above') {
                    if (mqttClientService) {
                        await mqttClientService.publish('home/default/device/fan/set', { action: 'on' });
                        actionTaken = 'turn_on_fan';
                    } else {
                        status = 'failed';
                        errorMsg = 'MQTT client not connected';
                    }
                }

                // Fire & forget log
                ThresholdTrace.create({
                    sensorId: `sensor_${sensorType}_1`,
                    sensorType,
                    value,
                    thresholdId: threshold.thresholdId,
                    thresholdName: threshold.name,
                    thresholdValue: threshold.max !== undefined ? threshold.max : threshold.min,
                    triggerDirection: direction,
                    actionTaken,
                    status,
                    errorMsg
                }).catch(err => console.error('[Log Error]', err));

            } catch (err) {
                console.error('[Alert Action Error]', err);
            }
        }
    }
};
