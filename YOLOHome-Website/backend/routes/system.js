import express from 'express';
import { SystemController } from '../controllers/systemController.js';

const router = express.Router();

router.get('/getall', SystemController.getAll);

export default router;
