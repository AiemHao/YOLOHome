import mongoose from 'mongoose';

const ControlTraceSchema = new mongoose.Schema(
  {
    timestamp:   { type: Date, default: Date.now, index: true },
    userId:      { type: String, default: 'anonymous' },
    source:      { type: String, enum: ['frontend','gateway','api-client'], required: true },
    action:      { type: String, required: true },               // e.g. "turn_on_fan"
    payload:     { type: mongoose.Schema.Types.Mixed },          // original request body
    mqttTopic:   { type: String },
    mqttPayload: { type: mongoose.Schema.Types.Mixed },
    status:      { type: String, enum: ['success','failure'], required: true },
    errorMsg:    { type: String }                               // populated only on failure
  },
  { collection: 'control_traces' }
);

export default mongoose.model('ControlTrace', ControlTraceSchema);
