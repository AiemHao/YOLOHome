import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import YAML from 'yaml';
import ThresholdTrace from '../models/ThresholdTrace.js';
import { Alert } from '../models/Alert.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const SENSOR_TYPE_MAP = {
    temp: 'temperature',
    temperature: 'temperature',
    humi: 'humidity',
    humidity: 'humidity',
    light: 'light'
};

const THRESHOLD_META = {
    temperature: {
        above: { thresholdId: 'temp_high', name: 'High Temperature', severity: 'WARNING' },
        below: { thresholdId: 'temp_low', name: 'Low Temperature', severity: 'WARNING' }
    },
    humidity: {
        above: { thresholdId: 'hum_high', name: 'High Humidity', severity: 'WARNING' },
        below: { thresholdId: 'hum_low', name: 'Low Humidity', severity: 'WARNING' }
    },
    light: {
        above: { thresholdId: 'light_bright', name: 'Bright Environment', severity: 'INFO' },
        below: { thresholdId: 'light_dark', name: 'Dark Environment', severity: 'INFO' }
    }
};

const DEFAULT_THRESHOLDS = {
    temperature: [
        { direction: 'above', value: 30, ...THRESHOLD_META.temperature.above }
    ],
    humidity: [
        { direction: 'above', value: 70, ...THRESHOLD_META.humidity.above },
        { direction: 'below', value: 65, ...THRESHOLD_META.humidity.below }
    ],
    light: [
        { direction: 'below', value: 30, ...THRESHOLD_META.light.below }
    ]
};

const getGatewayConfigPath = () => {
    if (process.env.GATEWAY_CONFIG_PATH) {
        return process.env.GATEWAY_CONFIG_PATH;
    }
    return path.resolve(__dirname, '..', '..', '..', 'YOLOHome-Gateway', 'config.yml');
};

const normalizeSensorType = (rawType) => {
    if (!rawType) {
        return null;
    }
    return SENSOR_TYPE_MAP[String(rawType).trim().toLowerCase()] || null;
};

const parseNumeric = (value) => {
    if (value === null || value === undefined) {
        return null;
    }
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
};

const buildThresholdEntry = (sensorType, direction, value) => {
    const meta = THRESHOLD_META[sensorType]?.[direction];
    if (!meta) {
        return null;
    }
    return {
        direction,
        value,
        thresholdId: meta.thresholdId,
        name: meta.name,
        severity: meta.severity
    };
};

const buildThresholdsFromConfig = (automationThresholds) => {
    const thresholdsBySensor = {};
    if (!automationThresholds || typeof automationThresholds !== 'object') {
        return thresholdsBySensor;
    }

    for (const [rawSensor, rules] of Object.entries(automationThresholds)) {
        const sensorType = normalizeSensorType(rawSensor);
        if (!sensorType || !Array.isArray(rules)) {
            continue;
        }

        for (const rule of rules) {
            if (!rule || typeof rule !== 'object') {
                continue;
            }

            const aboveValue = parseNumeric(rule.above);
            if (aboveValue !== null) {
                const entry = buildThresholdEntry(sensorType, 'above', aboveValue);
                if (entry) {
                    thresholdsBySensor[sensorType] = thresholdsBySensor[sensorType] || [];
                    thresholdsBySensor[sensorType].push(entry);
                }
            }

            const belowValue = parseNumeric(rule.below);
            if (belowValue !== null) {
                const entry = buildThresholdEntry(sensorType, 'below', belowValue);
                if (entry) {
                    thresholdsBySensor[sensorType] = thresholdsBySensor[sensorType] || [];
                    thresholdsBySensor[sensorType].push(entry);
                }
            }
        }
    }

    return thresholdsBySensor;
};

let thresholdsBySensor = { ...DEFAULT_THRESHOLDS };
let thresholdsLoadedAt = null;

const loadThresholdsFromGatewayConfig = async () => {
    const configPath = getGatewayConfigPath();
    try {
        const raw = await fs.readFile(configPath, 'utf8');
        const parsed = YAML.parse(raw) || {};
        const gatewayThresholds = parsed?.automation?.thresholds;
        const fromConfig = buildThresholdsFromConfig(gatewayThresholds);
        const merged = Object.keys(fromConfig).length > 0 ? fromConfig : DEFAULT_THRESHOLDS;
        thresholdsBySensor = merged;
        thresholdsLoadedAt = new Date();
        console.log('[Alert] Thresholds loaded from gateway config', { configPath });
    } catch (error) {
        thresholdsBySensor = { ...DEFAULT_THRESHOLDS };
        thresholdsLoadedAt = new Date();
        console.warn('[Alert] Failed to load gateway config, using defaults', {
            configPath,
            error: error.message
        });
    }
};

const buildAlertMessage = ({ sensorType, value, condition, thresholdValue, thresholdName }) => {
    return `Vượt ngưỡng: ${thresholdName}. Cảm biến=${sensorType}, giá trị=${value} ${condition} ${thresholdValue}`;
};

export const alertService = {
    processAlerts: async (topic, message) => {
        console.log('[Alert] Dummy processing for', topic);
    },
    getAlerts: async (query = {}, limit = 50, skip = 0) => {
        return Alert.find(query)
            .sort({ createdAt: -1 })
            .skip(skip)
            .limit(limit)
            .lean();
    },
    getActiveAlerts: async () => {
        return Alert.find({ isResolved: false })
            .sort({ createdAt: -1 })
            .lean();
    },
    resolveAlert: async (id) => {
        return Alert.findByIdAndUpdate(
            id,
            { isResolved: true, resolvedAt: new Date() },
            { new: true }
        );
    },
    deleteAlert: async (id) => {
        return Alert.findByIdAndDelete(id);
    },
    refreshThresholds: async () => {
        await loadThresholdsFromGatewayConfig();
        return {
            loadedAt: thresholdsLoadedAt,
            thresholds: thresholdsBySensor
        };
    },
    checkAndAlert: async (sensorType, value) => {
        if (!thresholdsLoadedAt) {
            await loadThresholdsFromGatewayConfig();
        }

        const thresholdRules = thresholdsBySensor[sensorType];
        if (!Array.isArray(thresholdRules) || thresholdRules.length === 0) {
            return;
        }
        for (const rule of thresholdRules) {
            if (!rule || typeof rule !== 'object') {
                continue;
            }

            const direction = rule.direction;
            const thresholdValue = rule.value;

            if (direction === 'above' && !(value > thresholdValue)) {
                continue;
            }

            if (direction === 'below' && !(value < thresholdValue)) {
                continue;
            }

            const condition = direction === 'above' ? '>' : '<';
            const thresholdName = rule.name || 'Threshold';

            const existingAlert = await Alert.findOne({
                type: sensorType,
                isResolved: false,
                condition,
                threshold: thresholdValue
            }).lean();

            if (existingAlert) {
                continue;
            }

            const message = buildAlertMessage({
                sensorType,
                value,
                condition,
                thresholdValue,
                thresholdName
            });

            await Alert.create({
                type: sensorType,
                severity: rule.severity || 'WARNING',
                message,
                value,
                threshold: thresholdValue,
                condition
            });

            ThresholdTrace.create({
                sensorId: `sensor_${sensorType}_1`,
                sensorType,
                value,
                thresholdId: rule.thresholdId || 'threshold',
                thresholdName: thresholdName,
                thresholdValue: thresholdValue,
                triggerDirection: direction,
                actionTaken: 'notify_only',
                status: 'executed',
                errorMsg: ''
            }).catch(err => console.error('[Log Error]', err));
        }
    }
};
