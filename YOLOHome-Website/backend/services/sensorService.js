import Sensor from '../models/Sensor.js';

export class SensorService {
    // Lấy snapshot 3 cảm biến gần nhất
    static async getLatestSensorData() {
        const latestSnapshot = await Sensor.findOne().sort({ timestamp: -1 });
        return latestSnapshot;
    }

    // Lưu snapshot 3 cảm biến tại cùng một timestamp
    static async saveSensorSnapshot(sensorData) {
        const newSensor = new Sensor({
            temperature: sensorData.temperature,
            humidity: sensorData.humidity,
            light: sensorData.light,
            timestamp: sensorData.timestamp || new Date()
        });
        return await newSensor.save();
    }

}
