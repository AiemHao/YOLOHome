import { DeviceService } from '../services/deviceService.js';
import { mqttService } from '../services/mqtt/mqttService.js';

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
        try {
            const {
                deviceName,
                deviceType,
                action,
                status
            } = req.body;

            // Validate input
            if ((!deviceName && !deviceType) || (action === undefined && status === undefined)) {
                return res.status(400).json({
                    success: false,
                    message: 'Cần deviceName/deviceType và action/status'
                });
            }

            const requestedAction = action ?? status;
            if (requestedAction !== 'on' && requestedAction !== 'off') {
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

            res.status(200).json({
                success: true,
                data: {
                    device: commandResult.deviceType || deviceType || deviceName,
                    action: requestedAction,
                    accepted: commandResult.published
                }
            });
        } catch (error) {
            next(error);
        }
    }
}
