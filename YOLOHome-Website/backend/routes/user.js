import express from 'express';
import { UserController } from '../controllers/userController.js';

const router = express.Router();

// User routes
router.post('/signup', UserController.signup);
router.post('/login', UserController.login);

export default router;