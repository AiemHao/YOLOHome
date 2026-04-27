import Device from '../models/Device.js';

const DEVICE_FIELD_BY_NAME = {
    Led: 'light',
    Fan: 'fan',
    Servo: 'servo'
};

const DEVICE_NAME_ORDER = ['Led', 'Fan', 'Servo'];

const toDeviceList = (snapshot) => {
    if (!snapshot) {
        return [];
    }

    return DEVICE_NAME_ORDER.map((deviceName) => {
        const field = DEVICE_FIELD_BY_NAME[deviceName];
        return {
            deviceName,
            status: snapshot[field],
            lastUpdated: snapshot.timestamp
        };
    });
};

export class DeviceService {
    // Lấy snapshot mới nhất và trả ra danh sách thiết bị
    static async getLatestDeviceData() {
        const latestSnapshot = await Device.findOne().sort({ timestamp: -1 });
        return toDeviceList(latestSnapshot);
    }

    // Lưu snapshot 3 trạng thái thiết bị tại cùng timestamp
    static async saveDeviceSnapshot(deviceData) {
        const newSnapshot = new Device({
            light: deviceData.light,
            fan: deviceData.fan,
            servo: deviceData.servo,
            timestamp: deviceData.timestamp || new Date()
        });

        return await newSnapshot.save();
    }
}
