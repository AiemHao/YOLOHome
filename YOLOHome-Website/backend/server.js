import express from 'express';
import cors from 'cors';

// ============================================
// IMPORTS
// ============================================
import config from './config/config.js';
import { connectDatabase, closeDatabase } from './config/database.js';
import { setupRoutes } from './routes/index.js';
import { mqttService } from './services/mqtt/mqttService.js';
import { seedDefaultData } from './services/seedData.js';
import { loggerMiddleware } from './middleware/logging.js';
import { notFoundHandler, errorHandler } from './middleware/errorHandler.js';

// ============================================
// INITIALIZE EXPRESS APP
// ============================================
const app = express();

// ============================================
// MIDDLEWARE
// ============================================
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(cors({
    origin: config.corsOrigin,
    credentials: true
}));
app.use(loggerMiddleware);

// ============================================
// ROUTES SETUP
// ============================================
setupRoutes(app);

// ============================================
// ERROR HANDLING MIDDLEWARE
// ============================================
app.use(notFoundHandler);
app.use(errorHandler);

// ============================================
// SERVER STARTUP
// ============================================
const startServer = async () => {
    try {
        // Connect to database
        await connectDatabase();
        await seedDefaultData();
        await mqttService.start();

        // Start listening
        const server = app.listen(config.port, () => {
            console.log(`Server is running at http://localhost:${config.port}`);
            console.log(`Environment: ${config.nodeEnv}`);
        });

        // Graceful shutdown
        const handleShutdown = async (signal) => {
            console.log(`\n${signal} signal received: closing HTTP server`);
            server.close(async () => {
                console.log('HTTP server closed');
                await mqttService.stop();
                await closeDatabase();
                process.exit(0);
            });
        };

        process.on('SIGTERM', () => handleShutdown('SIGTERM'));
        process.on('SIGINT', () => handleShutdown('SIGINT'));

    } catch (err) {
        console.error('Error starting server:', err);
        process.exit(1);
    }
};

// Start the server
startServer();

export default app;