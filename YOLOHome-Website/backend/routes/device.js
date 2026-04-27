import express from 'express';
import { DeviceController } from '../controllers/deviceController.js';

const router = express.Router();

// Device routes
router.get('/latest', DeviceController.getLatestData);
router.post('/control', DeviceController.controlDevice);

export default router;