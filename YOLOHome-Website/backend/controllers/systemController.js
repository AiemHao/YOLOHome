import { mqttService } from '../services/mqtt/mqttService.js';

const SYSTEM_STATE_KEYS = ['temp', 'humi', 'light', 'led', 'fan', 'servo'];

const normalizeSystemSnapshot = (raw) => {
    const snapshot = {};
    for (const key of SYSTEM_STATE_KEYS) {
        const value = raw?.[key];
        snapshot[key] = value === undefined || value === '' ? null : value;
    }
    return snapshot;
};

export class SystemController {
    static async getAll(req, res, next) {
        try {
            const result = await mqttService.sendGetAll();
            const snapshot = normalizeSystemSnapshot(result.response);

            res.status(200).json({
                success: true,
                data: snapshot
            });
        } catch (error) {
            if (error.message.includes('MQTT response timeout')) {
                return res.status(504).json({
                    success: false,
                    message: 'Gateway response timeout'
                });
            }
            next(error);
        }
    }
}
