import config from '../config/config.js';

// 404 Not Found middleware
export const notFoundHandler = (req, res) => {
    res.status(404).json({
        success: false,
        message: `Route không tìm thấy: ${req.method} ${req.path}`,
        timestamp: new Date().toISOString()
    });
};

// Global error handler
export const errorHandler = (err, req, res, next) => {
    const statusCode = err.statusCode || 500;
    const message = err.message || 'Lỗi server không xác định';

    console.error(`[ERROR] ${statusCode} - ${message}`);
    if (config.nodeEnv === 'development') {
        console.error(err);
    }

    res.status(statusCode).json({
        success: false,
        message: message,
        error: config.nodeEnv === 'development' ? err.message : undefined,
        timestamp: new Date().toISOString()
    });
};
