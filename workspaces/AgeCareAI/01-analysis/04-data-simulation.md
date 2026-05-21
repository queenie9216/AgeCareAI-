# AgeCareAI — Data Simulation Design

## Executive Summary

This document specifies the simulated data for all 4 AI layers of the AgeCareAI Streamlit application. Each layer's data is designed for realism within Singapore eldercare context, with inter-layer dependencies that support the typhoon scenario demonstration.

**Complexity:** Simple — all data is pre-generated, in-memory, no external dependencies.

---

## L1 — Fall Detection: Accelerometer Sequences

### Physical Parameters

| Parameter                  | Value                                             | Rationale                            |
| -------------------------- | ------------------------------------------------- | ------------------------------------ |
| Sampling rate              | 50 Hz                                             | Standard wearable accelerometer rate |
| Sequence duration          | 3 seconds                                         | Enough to capture full fall dynamics |
| Total samples per sequence | 150                                               | 50 Hz x 3 s                          |
| Axis order                 | X (lateral), Y (vertical), Z (anterior-posterior) | Standard wearable placement          |
| Magnitude units            | g (gravity = 1.0)                                 | Accelerometer standard output        |

### Realistic Magnitude Ranges (Singapore elderly, 65-90 years)

| Motion Type  | Vertical (Y)                                   | Lateral (X)                     | AP (Z)                          | Frequency Signature            |
| ------------ | ---------------------------------------------- | ------------------------------- | ------------------------------- | ------------------------------ |
| Resting      | 0.95-1.05 g                                    | -0.10 to +0.10 g                | -0.10 to +0.10 g                | Near-static, minimal variation |
| Normal walk  | 0.60-1.40 g                                    | -0.30 to +0.30 g                | -0.30 to +0.30 g                | ~2 Hz stride frequency         |
| Shuffle gait | 0.80-1.15 g                                    | -0.15 to +0.15 g                | -0.15 to +0.15 g                | ~1 Hz, reduced vertical range  |
| Fall event   | 0.10-0.50 g (pre-impact), 1.50-2.50 g (impact) | High rotation: -0.80 to +0.80 g | High rotation: -0.80 to +0.80 g | Broadband, chaotic post-impact |

### Sequence Specifications

#### Normal Walk Sequence

- **Duration:** 3 seconds
- **Pattern:** Rhythmic gait cycle at ~2 Hz (0.5 s per stride)
- **Vertical (Y):** Oscillates 0.60-1.40 g with each heel-strike peak
- **Lateral (X):** Minor oscillation -0.30 to +0.30 g (side-to-side sway)
- **AP (Z):** Consistent forward acceleration -0.30 to +0.30 g
- **Envelope:** Steady-state, no sudden transitions

#### Shuffle Gait Sequence

- **Duration:** 3 seconds
- **Pattern:** Slower cadence at ~1 Hz
- **Vertical (Y):** Compressed range 0.80-1.15 g (short steps, reduced lift)
- **Lateral (X):** Minimal -0.15 to +0.15 g
- **AP (Z):** Reduced -0.15 to +0.15 g
- **Envelope:** Smooth, reduced variance indicating cautious gait

#### Fall Event Sequence

- **Duration:** 3 seconds total
- **Phase 1 (0.0-0.5s):** Pre-fall normal gait deteriorating — Y drops from 1.0 to 0.7 g
- **Phase 2 (0.5-1.0s):** Sudden vertical drop — Y reaches 0.15 g (free-fall)
- **Phase 3 (1.0-1.5s):** Rotation during fall — X and Z show ±0.80 g oscillation
- **Phase 4 (1.5-2.0s):** Impact spike — all axes spike to 1.50-2.50 g with high variance
- **Phase 5 (2.0-3.0s):** Post-impact settling — rapid decay to near-zero with small residual tremor

### Implementation Parameters

```python
SEQUENCE_DURATION = 3.0          # seconds
SAMPLING_RATE = 50               # Hz
N_SAMPLES = 150                 # 3 * 50

# Normal walk — 2 Hz gait cycle
NORMAL_WALK_PARAMS = {
    "stride_frequency_hz": 2.0,
    "vertical_range": (0.60, 1.40),
    "lateral_range": (-0.30, 0.30),
    "ap_range": (-0.30, 0.30),
}

# Shuffle gait — slower, reduced range
SHUFFLE_GAIT_PARAMS = {
    "stride_frequency_hz": 1.0,
    "vertical_range": (0.80, 1.15),
    "lateral_range": (-0.15, 0.15),
    "ap_range": (-0.15, 0.15),
}

# Fall event — 5 phases
FALL_EVENT_PARAMS = {
    "pre_fall_duration": 0.5,      # phase 1
    "free_fall_duration": 0.5,     # phase 2
    "rotation_duration": 0.5,       # phase 3
    "impact_duration": 0.5,         # phase 4
    "settle_duration": 1.0,         # phase 5
    "free_fall_y_min": 0.10,
    "impact_g_max": 2.50,
    "rotation_amplitude": 0.80,
}
```

---

## L2 — Senior Health Data (20 Seniors)

### Demographic Distribution (Singapore Context)

| Age Band | Count | Distribution Rationale           |
| -------- | ----- | -------------------------------- |
| 65-69    | 4     | Young-elderly, relatively active |
| 70-74    | 5     | Moderate elderly                 |
| 75-79    | 5     | Higher morbidity onset           |
| 80-84    | 4     | Frailty increasing               |
| 85-90    | 2     | High-dependency                  |

### Ethnic Distribution (Singapore elderly population ratio)

| Ethnicity | Count | Singapore Elderly Ratio |
| --------- | ----- | ----------------------- |
| Chinese   | 14    | 70%                     |
| Malay     | 3     | 15%                     |
| Indian    | 2     | 10%                     |
| Other     | 1     | 5%                      |

### Health Parameter Ranges

| Parameter                          | Min | Max    | Clinical Basis                                              |
| ---------------------------------- | --- | ------ | ----------------------------------------------------------- |
| Age                                | 65  | 90     | Study scope                                                 |
| Resting Heart Rate (bpm)           | 60  | 100    | Normal sinus rhythm range                                   |
| SpO2 (%)                           | 90  | 100    | Clinical normal is 95-100%; 90-94% indicates mild hypoxemia |
| Sleep Duration (hours)             | 4   | 9      | Clinical: <5 or >9 associated with adverse outcomes         |
| Daily Step Count                   | 500 | 10,000 | Frail elderly: 500-2000; active: 5000-10000+                |
| Previous Hospitalisations (30-day) | 0   | 8      | Captures comorbidity burden                                 |
| Frailty Index                      | 0.0 | 1.0    | Clinical Frailty Scale mapping                              |

### Frailty Index Distribution

| CFS Score | Description                    | Simulated Range | Count |
| --------- | ------------------------------ | --------------- | ----- |
| 1-2       | Very Fit / Well                | 0.05-0.20       | 3     |
| 3-4       | Managing Well / Vulnerable     | 0.25-0.45       | 7     |
| 5-6       | Mildly / Moderately Frail      | 0.50-0.70       | 7     |
| 7-8       | Severely / Very Severely Frail | 0.75-0.95       | 3     |

### 30-Day Readmission Risk Stratification

| Risk Level | Criteria                                                        | Count |
| ---------- | --------------------------------------------------------------- | ----- |
| HIGH       | Frailty Index > 0.6 AND (SpO2 < 93 OR hospitalisations >= 3)    | 4     |
| MEDIUM     | Frailty Index 0.3-0.6 OR (SpO2 93-95 AND hospitalisations >= 2) | 8     |
| LOW        | Frailty Index < 0.3 AND SpO2 >= 96 AND hospitalisations <= 1    | 8     |

### Senior Roster (20 entries)

| ID  | Name              | Age | Ethnicity | HR  | SpO2 | Sleep | Steps | Hosp | Frailty | Risk   |
| --- | ----------------- | --- | --------- | --- | ---- | ----- | ----- | ---- | ------- | ------ |
| S01 | Tan Ah Bee        | 67  | Chinese   | 72  | 97   | 7.0   | 6500  | 0    | 0.15    | LOW    |
| S02 | Lim Mui Choo      | 69  | Chinese   | 68  | 98   | 7.5   | 8200  | 0    | 0.10    | LOW    |
| S03 | Ahmad bin Ismail  | 71  | Malay     | 78  | 96   | 6.5   | 4200  | 1    | 0.35    | MEDIUM |
| S04 | Wong Mei Ling     | 70  | Chinese   | 74  | 97   | 6.0   | 5800  | 0    | 0.30    | MEDIUM |
| S05 | Raj Kumar         | 73  | Indian    | 82  | 94   | 5.5   | 3100  | 2    | 0.50    | MEDIUM |
| S06 | Goh Poh Geok      | 75  | Chinese   | 76  | 95   | 6.5   | 4500  | 1    | 0.40    | MEDIUM |
| S07 | Fatimah bte Abdul | 78  | Malay     | 80  | 93   | 5.0   | 1800  | 3    | 0.65    | HIGH   |
| S08 | Chen Sok Hoon     | 74  | Chinese   | 70  | 97   | 7.5   | 7200  | 0    | 0.20    | LOW    |
| S09 | Lee Kim Huat      | 80  | Chinese   | 84  | 92   | 4.5   | 900   | 4    | 0.75    | HIGH   |
| S10 | boo Geok Hua      | 76  | Chinese   | 78  | 95   | 6.0   | 3800  | 2    | 0.55    | MEDIUM |
| S11 | Tan Siew Mei      | 82  | Chinese   | 86  | 91   | 4.0   | 600   | 5    | 0.85    | HIGH   |
| S12 | Sivaraman Nadesan | 68  | Indian    | 74  | 98   | 7.0   | 7500  | 0    | 0.15    | LOW    |
| S13 | Teo Chwee Lian    | 71  | Chinese   | 72  | 96   | 7.0   | 6100  | 1    | 0.35    | MEDIUM |
| S14 | Zaiton bte Osman  | 84  | Malay     | 88  | 90   | 4.5   | 500   | 6    | 0.90    | HIGH   |
| S15 | Ngiam Xiao Qing   | 66  | Chinese   | 66  | 99   | 8.0   | 9500  | 0    | 0.08    | LOW    |
| S16 | Gurdial Singh     | 77  | Indian    | 80  | 94   | 5.5   | 2200  | 3    | 0.60    | MEDIUM |
| S17 | Ang Hwee Ming     | 73  | Chinese   | 76  | 96   | 6.5   | 5400  | 1    | 0.40    | MEDIUM |
| S18 | Ho Li Ying        | 79  | Chinese   | 82  | 93   | 5.0   | 1500  | 4    | 0.70    | HIGH   |
| S19 | Tan Poh Lek       | 86  | Chinese   | 90  | 91   | 4.0   | 400   | 7    | 0.92    | HIGH   |
| S20 | Chew Wei Chen     | 65  | Chinese   | 64  | 98   | 8.5   | 10000 | 0    | 0.05    | LOW    |

---

## L3 — Caregiver Scheduling Data

### Senior Roster (10 Seniors for Scheduling)

Selected from L2 pool, with care needs and zone assignments:

| ID    | Name              | Care Needs                     | Zone    | Priority |
| ----- | ----------------- | ------------------------------ | ------- | -------- |
| SCH01 | Tan Ah Bee        | Companionship                  | North   | LOW      |
| SCH02 | Ahmad bin Ismail  | Mobility, Chronic Disease      | East    | MEDIUM   |
| SCH03 | Wong Mei Ling     | Post-op Recovery               | Central | HIGH     |
| SCH04 | Raj Kumar         | Chronic Disease, Physiotherapy | West    | MEDIUM   |
| SCH05 | Fatimah bte Abdul | Dementia, Mobility             | South   | HIGH     |
| SCH06 | Lee Kim Huat      | Chronic Disease, Mobility      | North   | HIGH     |
| SCH07 | Tan Siew Mei      | Dementia, Chronic Disease      | Central | HIGH     |
| SCH08 | Zaiton bte Osman  | Full Care                      | East    | HIGH     |
| SCH09 | Ho Li Ying        | Physiotherapy, Mobility        | West    | MEDIUM   |
| SCH10 | Tan Poh Lek       | Dementia, Full Care            | South   | CRITICAL |

### Singapore Planning Zone Classification

| Zone    | Districts                          | Description     |
| ------- | ---------------------------------- | --------------- |
| North   | Woodlands, Sembawang, Yishun       | Northern region |
| South   | Downtown Core, Outram, Bukit Merah | Central South   |
| East    | Tampines, Bedok, Pasir Ris         | Eastern region  |
| West    | Jurong, Clementi, Bukit Batok      | Western region  |
| Central | Toa Payoh, Bishan, Kallang         | City center     |

### Inter-Zone Travel Times (minutes)

| Origin \ Dest | North | South | East | West | Central |
| ------------- | ----- | ----- | ---- | ---- | ------- |
| North         | 10    | 45    | 35   | 40   | 25      |
| South         | 45    | 10    | 50   | 35   | 15      |
| East          | 35    | 50    | 10   | 45   | 30      |
| West          | 40    | 35    | 45   | 10   | 25      |
| Central       | 25    | 15    | 30   | 25   | 10      |

### Caregiver Roster (5 Caregivers)

| ID   | Name                    | Certifications                 | Home Zone | Max/Day | Hourly Slots |
| ---- | ----------------------- | ------------------------------ | --------- | ------- | ------------ |
| CG01 | Nurse Aileen Tan        | Nursing, Dementia Care         | North     | 3       | 4            |
| CG02 | Physio Daniel Lim       | Physiotherapy, Nursing         | East      | 3       | 4            |
| CG03 | Health Worker Mei Foo   | Dementia Care, Companionship   | Central   | 4       | 5            |
| CG04 | Nurse Siti Aminah       | Nursing, Chronic Disease       | West      | 3       | 4            |
| CG05 | Health Worker Raj Sethu | Companionship, Chronic Disease | South     | 4       | 5            |

### Certification Coverage Map

| Certification   | Covers Care Need          |
| --------------- | ------------------------- |
| Nursing         | All needs (full coverage) |
| Dementia Care   | Dementia, Companionship   |
| Physiotherapy   | Physiotherapy, Mobility   |
| Chronic Disease | Chronic Disease           |
| Companionship   | Companionship             |

### Care Need Assignment Constraints

| Senior           | Requires Certified CG                                    |
| ---------------- | -------------------------------------------------------- |
| Dementia         | CG01 (Nurse Aileen), CG03 (Mei Foo), or CG05 (Raj Sethu) |
| Full Care        | CG01 (Nurse Aileen) or CG04 (Nurse Siti)                 |
| Physiotherapy    | CG02 (Physio Daniel)                                     |
| Post-op Recovery | CG01, CG02, or CG04                                      |
| Chronic Disease  | CG01, CG04, or CG05                                      |
| Mobility         | Any CG with Nursing or Physio                            |
| Companionship    | CG03 or CG05                                             |

### Daily Schedule Windows

- **Morning:** 08:00-12:00 (4 slots of 1 hour each)
- **Afternoon:** 13:00-17:00 (4 slots of 1 hour each)
- **Each slot:** 1 senior visit (typical duration 45-60 min including travel)

---

## L4 — Event Scenarios

### Scenario 1: Mr Tan — Fall Confirmed (RED)

**Senior Profile:**

- Name: Tan Poh Lek (S19 from L2)
- Age: 86
- Zone: South
- Care needs: Dementia, Full Care
- Assigned caregiver: CG05 (Health Worker Raj Sethu, scheduled 14:00-15:00)
- Frailty index: 0.92 (Very Severely Frail)
- Risk level: HIGH

**Event Parameters:**
| Field | Value |
|-------|-------|
| Event type | Fall confirmed |
| Confidence | 0.91 |
| Timestamp | Today 13:47 |
| Sensor location | Left wrist wearable |
| Preceding activity | Walking to bathroom |

**L1 Reading at Event:**

- Y-axis shows free-fall pattern (0.12 g) followed by impact spike (2.3 g)
- X/Z rotation indicates lateral fall
- Duration of anomalous reading: 2.8 seconds

**Cascading Effects:**

- CG05's 14:00-15:00 slot with Tan Poh Lek is now a priority EMS response
- L3 must re-optimize: CG05 cannot take afternoon South-zone clients
- EMS dispatch to home address in South zone
- Emergency family contact (daughter: Tan Mei Hua, +65 9123 4567)

### Scenario 2: Mrs Lim — SpO2 Drop (AMBER)

**Senior Profile:**

- Name: Tan Siew Mei (S07 from L2)
- Age: 82
- Zone: Central
- Care needs: Dementia, Chronic Disease
- Assigned caregiver: CG03 (Health Worker Mei Foo, scheduled 09:00-10:00)
- Frailty index: 0.85
- Risk level: HIGH

**Event Parameters:**
| Field | Value |
|-------|-------|
| Event type | Vitals alert |
| SpO2 reading | 91% |
| Heart rate | 88 bpm |
| Timestamp | Today 08:23 |
| Trend | Declining over 2 hours (was 94% at 06:30) |

**Clinical Context:**

- SpO2 91% indicates mild hypoxemia
- For a senior with CHF history, this warrants observation
- Not an immediate emergency but requires same-day review

**Cascading Effects:**

- CG03's 09:00-10:00 visit elevated to include vitals check
- Family alert: son (Lim Chee Keong, +65 9234 5678)
- Polyclinic appointment booking triggered (Tan Tock Seng, 2pm slot available)
- L3 re-optimization: morning Central-zone slots become critical

### Scenario 3: Mr Ng — Missed Medication (GREEN)

**Senior Profile:**

- Name: Ho Li Ying (S18 from L2)
- Age: 79
- Zone: West
- Care needs: Physiotherapy, Mobility
- Assigned caregiver: CG04 (Nurse Siti Aminah, scheduled 11:00-12:00)
- Frailty index: 0.70
- Risk level: HIGH

**Event Parameters:**
| Field | Value |
|-------|-------|
| Event type | Medication missed |
| Medication | Metformin 500mg (morning dose) |
| Timestamp | Today 08:00 (dose due) |
| Confirmation | Smart pill bottle did not open |
| Previous adherence | 78% (borderline) |

**Cascading Effects:**

- CG04's 11:00-12:00 visit to include medication compliance check
- Reminder alert sent to senior's phone
- No re-optimization required for L3
- Family notification (wife: Ho Ah Ma, +65 9345 6789) — informational only

### Typhoon Scenario: Compound Event

**Trigger:** "Trigger Typhoon Scenario" button on L4

**Compound Event:**

1. Tan Poh Lek (S19) falls at 13:47 (RED — same as Scenario 1)
2. CG05 (Health Worker Raj Sethu) calls in sick at 13:50
   - Cannot cancel without notice (no-show protocol triggers)

**L3 Response (within 1 second):**

- Remove CG05 from afternoon schedule
- Re-assign Tan Poh Lek's 14:00 slot to CG01 (Nurse Aileen Tan, North zone, available)
- Re-optimize South-zone coverage (Tan Poh Lek moved to EMS protocol, not CG visit)
- All other CG05 assignments redistributed:
  - SCH01 (North): stays with CG01 (already overlapping North)
  - SCH05 (South, Dementia): transferred to CG03 (available, Central)
  - SCH10 (South, Full Care): transferred to CG01 (available, high-priority override)

**L4 Response (simultaneous with L3):**

- EMS dispatched for Tan Poh Lek (13:47 trigger)
- CG05 sick day logged, no afternoon coverage for SCH01, SCH05, SCH10
- All three South/Central clients receive family notification
- New schedule pushed to CG01, CG03 apps within same-second window

---

## Inter-Layer Dependency Map

```
L4 Event Triggers
    |
    +---> L3 Re-optimisation (caregiver schedule)
    |         |
    |         +---> Zone constraints
    |         +---> Certification matching
    |         +---> Max seniors/caregiver/day
    |
    +---> L2 Health Update (senior risk profile)
              |
              +---> SpO2 trend affects risk score
              +---> Hospitalisation count updates

L1 Accelerometer Data
    |
    +---> L4 Fall Event Classification
              |
              +---> Confidence >= 0.85 --> RED alert
              +---> Triggers EMS + family + L3 schedule review
```

---

## Data Generation Code Structure

### L1 Generator: `generate_accelerometer_sequence(seq_type, duration=3.0, fs=50)`

Returns: `np.ndarray` of shape (N_SAMPLES, 3) with columns [X, Y, Z]

### L2 Generator: `generate_senior_health_data(n=20)`

Returns: `pd.DataFrame` with columns matching senior roster schema

### L3 Generator: `generate_scheduling_data(seniors, caregivers)`

Returns: tuple of (senior_assignments, caregiver_schedules, zone_matrix)

### L4 Generator: `generate_event_scenario(scenario_id)`

Returns: `dict` with event fields + cascading_effects structure

---

## Simulation Constants

```python
# Temporal
SIMULATION_DATE = "2024-01-15"  # Representative Singapore weekday
MORNING_WINDOW = (8, 12)         # 08:00-12:00
AFTERNOON_WINDOW = (13, 17)      # 13:00-17:00

# Zones
ZONES = ["North", "South", "East", "West", "Central"]
ZONE_TRAVEL_MATRIX = {...}       # As specified above

# Caregiver capacity
MAX_VISITS_PER_CAREGIVER = 4     # Per day
SLOT_DURATION_HOURS = 1.0

# L1 Signal
ACCEL_FS = 50                    # Hz
GRAVITY = 1.0                    # g

# L2 Thresholds
SPO2_CRITICAL = 90               # Below this = HIGH concern
SPO2_WARNING = 93                # Below this = AMBER concern
FRAILTY_HIGH = 0.6              # Above this + comorbidity = HIGH risk
HOSPITALISATION_HIGH = 3        # Above this = HIGH risk factor

# L4 Decision Thresholds
FALL_CONFIDENCE_RED = 0.85      # EMS + full alert
SPO2_AMBER = 93                 # Family alert + polyclinic
MEDICATION_MISSED = 1           # Single missed dose = reminder
```
