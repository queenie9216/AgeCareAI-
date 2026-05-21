# L1 — Fall Detection Specification

## Overview

Real-time fall detection from simulated wearable accelerometer data using a lightweight CNN classifier.

## Data Specification

### Accelerometer Stream

- **Sampling Rate:** 50 Hz (50 samples per second)
- **Axes:** X (lateral), Y (vertical), Z (anterior-posterior)
- **Format:** Time-series buffer of fixed window size

### Pre-loaded Sequences

| Sequence     | Duration  | Characteristics                                                                       |
| ------------ | --------- | ------------------------------------------------------------------------------------- |
| Normal Walk  | 3 seconds | Regular stride pattern, consistent vertical oscillation ~1g, minimal lateral movement |
| Shuffle Gait | 3 seconds | Short steps, reduced vertical range (~0.5g variance), shuffling motion                |
| Fall Event   | 3 seconds | Sudden vertical drop, rotation, impact spike                                          |

### Signal Characteristics

- Normal walking: vertical acceleration oscillates 0.8-1.2g, lateral < 0.3g
- Shuffle gait: reduced amplitude, irregular pattern, < 0.5g vertical variance
- Fall: free-fall phase (< 0.3g), followed by impact spike (> 2g), possible rotation

## Model Architecture

### CNN Classifier

- **Input:** 1D sliding window (150 samples × 3 axes = 450 features per window)
- **Architecture:** Lightweight 1D CNN
  - Conv1D layer 1: 32 filters, kernel size 5, ReLU
  - MaxPooling1D: pool size 2
  - Conv1D layer 2: 64 filters, kernel size 3, ReLU
  - GlobalAveragePooling1D
  - Dense: 3 units (softmax output)
- **Output:** Probability distribution over [Normal Walk, Shuffle Gait, Fall]

### Alternative: sklearn Random Forest

- If PyTorch unavailable, use RandomForestClassifier with extracted statistical features
- Features: mean, std, min, max, range, zero-crossings per axis

## Classification Logic

### Real-time Processing

1. Maintain circular buffer of last 150 samples (3 seconds at 50Hz)
2. Every new sample: run inference on full buffer
3. Output: class prediction + confidence score

### Alert Threshold

- **Fall Alert Trigger:** fall_confidence ≥ 0.85
- **Alert Types:**
  - ≥ 0.85: HIGH alert (immediate attention)
  - 0.70-0.84: MEDIUM alert (warning)
  - < 0.70: LOW (normal monitoring)

## UI Components

### L1 Streamlit Page

1. **Sequence Selector** - Radio buttons: Normal Walk | Shuffle Gait | Fall
2. **Live Data Display** - Line chart showing 3-axis accelerometer data
3. **Classification Log** - Table with columns: Timestamp, Predicted Class, Confidence, Alert
4. **Visual Alert** - Red banner when fall_confidence ≥ 0.85
5. **Confidence Gauge** - Plotly gauge showing current confidence

## State Management

- Session state stores: current_sequence, classification_history, alert_triggered
- Buffer managed as numpy array with index wraparound

## Simulated Data Generation

```python
def generate_walk(timesteps=150):
    # Normal walk: sin wave + noise for vertical oscillation
    t = np.linspace(0, 3, timesteps)
    y = 1.0 + 0.2 * np.sin(2 * np.pi * 2 * t) + noise
    x = 0.1 * np.sin(2 * np.pi * 1 * t) + noise
    z = 0.05 * np.sin(2 * np.pi * 0.5 * t) + noise

def generate_fall(timesteps=100):
    # Free fall (0-0.5s) -> Impact (0.5s) -> Settle (0.5s)
    # y drops to ~0.2g, then spikes to ~2.5g, then settles
```
