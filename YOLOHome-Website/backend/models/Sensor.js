import mongoose from 'mongoose';

const SensorSchema = new mongoose.Schema({
    temperature: {
        type: Number,
        required: true
    },
    humidity: {
        type: Number,
        required: true
    },
    light: {
        type: Number,
        required: true
    },
    timestamp: { 
        type: Date, 
        default: Date.now // Tự động lưu thời gian khi dữ liệu đẩy lên
    }
});

export default mongoose.model('Sensor', SensorSchema);