import { SensorService } from '../services/sensorService.js';

export class SensorController {
    // Lấy snapshot 3 sensor gần nhất
    static async getLatestData(req, res, next) {
        try {
            const latestData = await SensorService.getLatestSensorData();
            res.status(200).json({
                success: true,
                data: latestData
            });
        } catch (error) {
            next(error);
        }
    }
}
