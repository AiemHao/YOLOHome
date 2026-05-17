import { alertService } from '../services/alertService.js';

export const getAlerts = async (req, res, next) => {
    try {
        const { isResolved, limit = 50, skip = 0 } = req.query;
        let query = {};
        
        if (isResolved !== undefined) {
            query.isResolved = isResolved === 'true';
        }

        const alerts = await alertService.getAlerts(query, parseInt(limit), parseInt(skip));
        res.json({
            success: true,
            count: alerts.length,
            data: alerts
        });
    } catch (error) {
        next(error);
    }
};

export const getActiveAlerts = async (req, res, next) => {
    try {
        const alerts = await alertService.getActiveAlerts();
        res.json({
            success: true,
            count: alerts.length,
            data: alerts
        });
    } catch (error) {
        next(error);
    }
};

export const resolveAlert = async (req, res, next) => {
    try {
        const { id } = req.params;
        const alert = await alertService.resolveAlert(id);
        
        if (!alert) {
            return res.status(404).json({ success: false, message: 'Alert not found' });
        }

        res.json({
            success: true,
            data: alert
        });
    } catch (error) {
        next(error);
    }
};

export const deleteAlert = async (req, res, next) => {
    try {
        const { id } = req.params;
        const alert = await alertService.deleteAlert(id);
        
        if (!alert) {
            return res.status(404).json({ success: false, message: 'Alert not found' });
        }

        res.json({
            success: true,
            message: 'Alert deleted successfully'
        });
    } catch (error) {
        next(error);
    }
};
