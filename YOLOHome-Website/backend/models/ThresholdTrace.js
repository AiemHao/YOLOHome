import mongoose from 'mongoose';

const ThresholdTraceSchema = new mongoose.Schema(
  {
    timestamp:          { type: Date, default: Date.now, index: true },
    sensorId:           { type: String, required: true },
    sensorType:         { type: String, required: true },   // temperature, humidity, light, …
    value:              { type: Number, required: true },   // actual reading
    thresholdId:        { type: String, required: true },
    thresholdName:      { type: String, required: true },   // from docs/threshold_mapping.md
    thresholdValue:     { type: Number, required: true },
    triggerDirection:   { type: String, enum: ['above','below'], required: true },
    actionTaken:        { type: String, required: true },   // e.g. "publish_mqtt"
    status:             { type: String, enum: ['executed','failed'], required: true },
    errorMsg:           { type: String }                    // if action failed
  },
  { collection: 'threshold_traces' }
);

export default mongoose.model('ThresholdTrace', ThresholdTraceSchema);
