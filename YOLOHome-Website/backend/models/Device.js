import mongoose from 'mongoose';

const DeviceSchema = new mongoose.Schema({
    light: {
        type: String,
        required: true,
        enum: ['on', 'off']
    },
    fan: {
        type: String,
        required: true,
        enum: ['on', 'off']
    },
    servo: {
        type: String,
        required: true,
        enum: ['on', 'off']
    },
    timestamp: {
        type: Date,
        default: Date.now 
    }
});

export default mongoose.model('Device', DeviceSchema);