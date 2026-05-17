# Threshold Mapping

This document maps threshold IDs used in the system to human-readable names and descriptions. This mapping should be referenced when populating the `thresholdName` field in the `ThresholdTrace` logs.

| Threshold ID | Human-Readable Name | Description |
|--------------|--------------------|-------------|
| `temp_high`  | High Temperature   | Triggered when temperature exceeds the configured upper limit (e.g., > 30 °C). |
| `temp_low`   | Low Temperature    | Triggered when temperature drops below the configured lower limit. |
| `hum_high`   | High Humidity      | Triggered when humidity exceeds the configured upper limit. |
| `hum_low`    | Low Humidity       | Triggered when humidity drops below the configured lower limit (e.g., < 30 %). |
| `light_dark` | Dark Environment   | Triggered when light level drops below the configured lower limit (e.g., < 200 lux). |
| `light_bright`| Bright Environment| Triggered when light level exceeds the configured upper limit. |
