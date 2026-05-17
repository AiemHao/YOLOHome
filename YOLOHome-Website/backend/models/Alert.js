import mongoose from 'mongoose';

const alertSchema = new mongoose.Schema({
    type: {
        type: String,
        required: true,
        enum: ['temperature', 'humidity', 'light', 'system']
    },
    severity: {
        type: String,
        required: true,
        enum: ['INFO', 'WARNING', 'CRITICAL']
    },
    message: {
        type: String,
        required: true
    },
    value: {
        type: Number,
        required: true
    },
    threshold: {
        type: Number
    },
    condition: {
        type: String, // e.g., '>', '<'
    },
    isResolved: {
        type: Boolean,
        default: false
    },
    resolvedAt: {
        type: Date
    },
    createdAt: {
        type: Date,
        default: Date.now,
        expires: 604800 // TTL Index: Auto delete after 7 days (7 * 24 * 60 * 60 seconds)
    }
});

// Index for querying active alerts efficiently
alertSchema.index({ isResolved: 1, createdAt: -1 });

export const Alert = mongoose.model('Alert', alertSchema);
