// backend/routes/voiceRoutes.js
import express from 'express';
import multer from 'multer';
import { handleVoiceCommand } from '../services/voiceService.js';

const router = express.Router();

// Configure multer to store uploaded audio in memory (buffer)
const storage = multer.memoryStorage();
const upload = multer({ storage, limits: { fileSize: 5 * 1024 * 1024 } }); // 5 MB limit

/**
 * POST /api/voice/command
 * Accepts a single audio file (field name: "audio") and returns transcription + intent.
 */
router.post('/command', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ status: 'error', message: 'No audio file uploaded' });
    }
    const result = await handleVoiceCommand(req.file);
    res.json({ status: 'success', data: result });
  } catch (err) {
    console.error('[VOICE] Service error:', err);
    res.status(500).json({ status: 'error', message: err.message || 'Internal server error' });
  }
});

export default router;
