import sensorRoutes from './sensor.js';
import deviceRoutes from './device.js';
import userRoutes from './user.js';
import systemRoutes from './system.js';
import alertRoutes from './alert.js';
import voiceRoutes from './voiceRoutes.js';

export const setupRoutes = (app) => {
    // Health check endpoint
    app.get('/health', (req, res) => {
        res.status(200).json({
            status: 'OK',
            message: 'Server Backend YOLOHome is running...',
            timestamp: new Date().toISOString()
        });
    });

    // API Routes
    app.use('/api/users', userRoutes);
    app.use('/api/devices', deviceRoutes);
    app.use('/api/sensors', sensorRoutes);
    app.use('/api/system', systemRoutes);
    app.use('/api/alerts', alertRoutes);
    // console.log('Mounting /api/voice with:', voiceRoutes ? 'Router exists' : 'UNDEFINED');
    app.use('/api/voice', voiceRoutes);
};
