import { DeviceService } from '../services/deviceService.js';
import { mqttService } from '../services/mqtt/mqttService.js';
import ControlTrace from '../models/ControlTrace.js';

const logControlTrace = (trace) => {
    ControlTrace.create(trace).catch((err) => console.error('[Log Error]', err));
};

export class DeviceController {
    // Lấy snapshot trạng thái 3 thiết bị gần nhất
    static async getLatestData(req, res, next) {
        try {
            const devices = await DeviceService.getLatestDeviceData();
            res.status(200).json({
                success: true,
                data: devices
            });
        } catch (error) {
            next(error);
        }
    }

    // Điều khiển thiết bị (cập nhật trạng thái)
    static async controlDevice(req, res, next) {
        const traceBase = {
            userId: req.user?.id || 'anonymous',
            source: 'frontend',
            action: 'device_control',
            payload: req.body
        };

        try {
            const {
                deviceName,
                deviceType,
                action,
                status
            } = req.body;

            // Validate input
            if ((!deviceName && !deviceType) || (action === undefined && status === undefined)) {
                logControlTrace({
                    ...traceBase,
                    status: 'failure',
                    errorMsg: 'Missing device identifier or action'
                });
                return res.status(400).json({
                    success: false,
                    message: 'Cần deviceName/deviceType và action/status'
                });
            }

            const requestedAction = action ?? status;
            if (requestedAction !== 'on' && requestedAction !== 'off') {
                logControlTrace({
                    ...traceBase,
                    status: 'failure',
                    errorMsg: 'Invalid action: must be on/off'
                });
                return res.status(400).json({
                    success: false,
                    message: 'Chỉ chấp nhận đúng action "on" hoặc "off"'
                });
            }

            const commandResult = await mqttService.sendDeviceCommand({
                deviceType,
                deviceName,
                action,
                status
            });

            const normalizedDevice = (commandResult.deviceType || deviceType || deviceName || '').toLowerCase();
            const fieldByDevice = {
                led: 'light',
                light: 'light',
                fan: 'fan',
                servo: 'servo'
            };

            const field = fieldByDevice[normalizedDevice];
            if (field) {
                const latestSnapshot = await DeviceService.getLatestSnapshot();
                await DeviceService.saveDeviceSnapshot({
                    light: latestSnapshot?.light ?? null,
                    fan: latestSnapshot?.fan ?? null,
                    servo: latestSnapshot?.servo ?? null,
                    [field]: requestedAction,
                    timestamp: new Date()
                });
            }

            logControlTrace({
                ...traceBase,
                action: `device_${commandResult.deviceType || deviceType || deviceName}_${requestedAction}`,
                mqttTopic: commandResult.topic,
                mqttPayload: commandResult.mqttPayload,
                status: commandResult.published ? 'success' : 'failure',
                errorMsg: commandResult.published ? undefined : 'MQTT publish skipped'
            });

            res.status(200).json({
                success: true,
                data: {
                    device: commandResult.deviceType || deviceType || deviceName,
                    action: requestedAction,
                    accepted: commandResult.published
                }
            });
        } catch (error) {
            logControlTrace({
                ...traceBase,
                status: 'failure',
                errorMsg: error.message
            });
            next(error);
        }
    }
}
