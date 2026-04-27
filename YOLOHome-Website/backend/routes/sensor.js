import express from 'express';
import { SensorController } from '../controllers/sensorController.js';

const router = express.Router();

// Sensor routes
router.get('/latest', SensorController.getLatestData);

export default router;