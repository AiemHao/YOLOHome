import express from 'express';
import {
	getAlerts,
	getActiveAlerts,
	resolveAlert,
	deleteAlert
} from '../controllers/alertController.js';

const router = express.Router();

router.get('/', getAlerts);
router.get('/active', getActiveAlerts);
router.patch('/:id/resolve', resolveAlert);
router.delete('/:id', deleteAlert);

export default router;
