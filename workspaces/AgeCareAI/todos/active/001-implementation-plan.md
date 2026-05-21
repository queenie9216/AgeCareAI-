# AgeCareAI Implementation Todos

## Project: AgeCareAI — Autonomous Elder Care Platform

**Tech Stack:** Python · Streamlit · XGBoost · SHAP · OR-Tools · scikit-learn · numpy · pandas · plotly
**Architecture:** Single `app.py` with sidebar navigation between 4 layers

---

## Approved Design Decisions

| OD     | Decision                      | Choice                                             |
| ------ | ----------------------------- | -------------------------------------------------- |
| OD-001 | L1 CNN Architecture           | **sklearn RandomForest** with statistical features |
| OD-002 | L2 SHAP Fallback              | **Simplified bar chart** on explainer failure      |
| OD-003 | L4 Typhoon Debounce           | **5 second disable** after trigger                 |
| OD-004 | L4 NEHR Log Format            | **Structured JSON** entries                        |
| OD-005 | L3 Schedule Conflict Priority | **Certification match** over zone preference       |

---

## Milestone 1: Project Foundation

### M1.1: Project Setup

- [ ] **Create `requirements.txt`** with: streamlit, xgboost, shap, ortools, scikit-learn, numpy, pandas, plotly, torch (minimal install)
  - Implements: `specs/data-models.md` (dependencies)
- [ ] **Verify all packages install** with `pip install -r requirements.txt`
- [ ] **Create `app.py`** with Streamlit page configuration and sidebar navigation structure
  - Implements: `specs/integration.md` (app shell, navigation)

### M1.2: Data Models and Enums

- [ ] **Create data models module** (`app.py` section): `Senior`, `SeniorFeatures`, `Caregiver`, `Zone`, `Day`, `Event`, `EventType`, `RiskBand`, `RiskLevel`, `SHAPFactor`, `ScheduleAssignment`, `SeniorAssignment`
  - Implements: `specs/data-models.md` (all dataclasses)
- [ ] **Implement Zone enum**: NORTH, SOUTH, EAST, WEST, CENTRAL
- [ ] **Implement Day enum**: MON, TUE, WED, THU, FRI
- [ ] **Implement EventType enum**: FALL, VITALS, MEDICATION
- [ ] **Implement RiskBand enum**: RED, AMBER, GREEN

---

## Milestone 2: Simulated Data Generation

### M2.1: Singapore Senior Dataset (20 seniors)

- [ ] **Generate 20 senior records** with realistic Singapore demographics
  - Chinese/Malay/Indian distribution (70/15/10/5%)
  - Names: Singaporean Chinese (Tan, Lee, Lim, Ng, Wong, Chen, Goh, Koh, Teo, Ang), Malay (Abdul, Fatimah, Rahim, Aminah, Ibrahim, Zainab), Indian (Nair, Patel, Singh, Raman, Kumari)
  - Ages: 65-90, skewed toward 70-85
  - Features: age, resting_hr (55-100), spo2 (88-100), sleep_hours (3.5-9), step_count (500-10000), prev_hospitalisations (0-8), frailty_index (0.0-1.0)
  - Correct typo: "boo Geok Hua" → "Boo Geok Hua"
  - Implements: `specs/data-models.md` § Senior, `specs/L2-health-risk.md` § Dataset Specification

### M2.2: Accelerometer Sequences (L1)

- [ ] **Generate normal walk sequence**: 150 samples (3s @ 50Hz), 3-axis accelerometer data
  - Y (vertical): sin wave 0.8-1.2g, X/Z: <0.3g noise
  - Implements: `specs/L1-fall-detection.md` § Pre-loaded Sequences
- [ ] **Generate shuffle gait sequence**: 150 samples, reduced vertical range ~0.5g variance
- [ ] **Generate fall event sequence**: 150 samples, 5-phase model (pre-fall → free-fall ~0.2g → rotation → impact ~2.5g → settle)

### M2.3: Caregiver and Senior Scheduling Data (L3)

- [ ] **Define 10 seniors** with: id, name, care_needs (list), zone, care_hours
  - Care needs mapping: Dementia, Chronic Disease, Post-Op, Mobility Support, Companion
  - Implements: `specs/L3-schedule-optimization.md` § Seniors
- [ ] **Define 5 caregivers** with: id, name, certifications (list), home_zone, availability (list of days)
  - Certifications: Nursing, Dementia Care, Chronic Disease, Post-Op, Mobility, Companion
  - Implements: `specs/L3-schedule-optimization.md` § Caregivers

### M2.4: Event Scenarios (L4)

- [ ] **Pre-load event E1**: Tan Poh Lek (78), Fall Detected, confidence 0.91, RED risk
- [ ] **Pre-load event E2**: Lim Sok Kuan (72), SpO2 91%, AMBER risk
- [ ] **Pre-load event E3**: Ng Teck Seng (80), missed 2 medication doses, GREEN risk
  - Implements: `specs/L4-care-agent.md` § Pre-loaded Events

---

## Milestone 3: L1 — Fall Detection

### M3.1: Feature Extraction

- [ ] **Extract statistical features** per axis: mean, std, min, max, range, zero-crossings
  - Total: 18 features per window (6 stats × 3 axes)
  - Implements: `specs/L1-fall-detection.md` § sklearn Random Forest
- [ ] **Build sliding window buffer** (150 samples, circular index)

### M3.2: sklearn Random Forest Classifier

- [ ] **Train RandomForestClassifier** on synthetic labeled data (normal/shuffle/fall)
  - n_estimators=100, max_depth=10, random_state=42
  - Pre-train at app init, store model in session_state
  - Implements: `specs/L1-fall-detection.md` § Model Architecture
- [ ] **Implement `classify_sequence(buffer)`** returning {label, confidence}

### M3.3: Streamlit UI Components

- [ ] **Sequence selector** radio buttons: Normal Walk | Shuffle Gait | Fall
- [ ] **Live line chart** (plotly) showing 3-axis accelerometer data updating in real-time
- [ ] **Classification log table**: Timestamp, Predicted Class, Confidence, Alert
- [ ] **Visual alert banner** (red) when fall_confidence >= 0.85
- [ ] **Confidence gauge** (plotly) showing current confidence per class
- [ ] **Real-time update loop** using st.empty placeholder + sleep(0.02) for 50Hz

---

## Milestone 4: L2 — Health Risk Dashboard

### M4.1: XGBoost Model Training

- [ ] **Prepare 20-senior dataset** with 7 features
- [ ] **Generate ground-truth labels** based on clinical rules:
  - HIGH: frailty_index > 0.6 OR spo2 < 92 OR prev_hospitalisations >= 4
  - MEDIUM: frailty_index > 0.4 OR spo2 < 95 OR prev_hospitalisations >= 2
  - LOW: all other
- [ ] **Train XGBClassifier** (n_estimators=100, max_depth=4, objective='multi:softprob', num_class=3)
  - Implements: `specs/L2-health-risk.md` § Model Specification

### M4.2: SHAP Integration

- [ ] **Build SHAP TreeExplainer** on trained XGBoost model at init
- [ ] **Compute SHAP values** for each senior record
- [ ] **Extract top 3 factors** per senior (sorted by absolute SHAP value)
- [ ] **Implement fallback**: On explainer failure, show feature importance bar chart
  - Implements: `specs/L2-health-risk.md` § SHAP Integration

### M4.3: Streamlit UI Components

- [ ] **Traffic-light risk table**: Senior Name, Age, Risk Level (🔴 HIGH/🟡 MEDIUM/🟢 LOW), Risk Score, Top 3 Factors
  - Color coding: #d62728 (red), #ff7f0e (amber), #2ca02c (green)
  - Sorted by risk_score descending (high → low)
  - Implements: `specs/L2-health-risk.md` § UI Components
- [ ] **SHAP detail panel**: Select senior → force plot + top 3 bars with directional arrows
- [ ] **Summary statistics**: Risk distribution pie chart, high-risk count

---

## Milestone 5: L3 — Caregiver Schedule Optimiser

### M5.1: OR-Tools MILP Solver

- [ ] **Define decision variables**: x[i,j] ∈ {0,1} for caregiver i assigned to senior j
- [ ] **Implement hard constraints**:
  - Certification match: x[i,j] ≤ certified[i,j]
  - Max 2 seniors/day: Σx[i,j] ≤ 2
  - Availability: x[i,j] ≤ available[i,j]
- [ ] **Implement soft constraint**: Zone preference penalty (same-zone preferred)
- [ ] **Implement solver** using OR-Tools CP-SAT
  - Return: optimal assignments, objective value, solve time
  - Handle infeasible: return "No feasible schedule" message
  - Implements: `specs/L3-schedule-optimization.md` § MILP Formulation

### M5.2: Streamlit UI Components

- [ ] **Schedule table display**: Rows = Caregivers, Columns = assigned seniors (name, care type, zone)
  - Color coding: green (same zone), yellow (different zone)
  - Implements: `specs/L3-schedule-optimization.md` § UI Components
- [ ] **Caregiver status cards**: Show active caregivers with assignment count
- [ ] **"Caregiver cancels" button** per caregiver:
  - Marks caregiver unavailable
  - Re-runs solver
  - Displays new schedule
  - Shows solve time in milliseconds
  - Implements: `specs/L3-schedule-optimization.md` § Real-Time Re-optimisation

### M5.3: Performance Target

- [ ] **Initial solve**: < 1000ms
- [ ] **Re-solve (cancel)**: < 500ms
- [ ] **Display solve time** in UI

---

## Milestone 6: L4 — Care Agent

### M6.1: Decision Tree Logic

- [ ] **Implement decision rules**:
  ```
  IF event_type == FALL AND risk_profile == RED:
      actions = [EMS_DISPATCH, FAMILY_ALERT, NEHR_LOG]
  ELIF event_type == SPO2_DROP AND risk_profile == AMBER:
      actions = [FAMILY_ALERT, POLYCLINIC_BOOKING]
  ELIF event_type == MISSED_MEDS AND risk_profile == GREEN:
      actions = [SEND_REMINDER]
  ELIF event_type == FALL AND risk_profile == AMBER:
      actions = [FAMILY_ALERT, AMBULANCE_STANDBY, NEHR_LOG]
  ELIF event_type == SPO2_DROP AND risk_profile == RED:
      actions = [EMS_DISPATCH, FAMILY_ALERT, NEHR_LOG, POLYCLINIC_EMERGENCY]
  ELSE:
      actions = [LOG_ONLY, SCHEDULE_CHECK]
  ```

  - Implements: `specs/L4-care-agent.md` § Decision Tree Logic

### M6.2: Action Definitions

- [ ] **Implement action functions**:
  - `EMS_DISPATCH`: Log "Dispatching EMS to [zone]"
  - `FAMILY_ALERT`: Log "Alerting family: +65 XXXX XXXX"
  - `NEHR_LOG`: Log JSON entry {timestamp, action, senior, details}
  - `POLYCLINIC_BOOKING`: Log "Booking polyclinic appointment"
  - `SEND_REMINDER`: Log "Sending medication reminder"
  - `AMBULANCE_STANDBY`: Log "Ambulance on standby"
  - `LOG_ONLY`: Log "Event logged for monitoring"
  - `SCHEDULE_CHECK`: Log "Scheduling welfare check"
  - Implements: `specs/L4-care-agent.md` § Action Definitions

### M6.3: Streamlit UI Components

- [ ] **Event feed display**: Real-time table (Time, Senior, Event, Severity, Status, Actions)
  - Auto-scroll to latest
  - Implements: `specs/L4-care-agent.md` § Event Feed Display
- [ ] **Perception → Reasoning → Action visual**: 3-step expandable display
  - Step 1 (Perception): raw event data
  - Step 2 (Reasoning): rule matched + factors
  - Step 3 (Action): actions taken with timestamps
  - Implements: `specs/L4-care-agent.md` § Reasoning Visualization
- [ ] **Event trigger buttons**: One per pre-loaded event (E1, E2, E3)

---

## Milestone 7: Integration (Typhoon Scenario)

### M7.1: Cross-Layer State Management

- [ ] **Implement shared `st.session_state`**:
  - `l1_sequence`, `l1_classification_log`, `l1_alert_triggered`
  - `l2_seniors_df`, `l2_risk_predictions`, `l2_shaps`
  - `l3_schedule`, `l3_active_caregivers`, `l3_solve_time_ms`
  - `l4_event_log`, `l4_actions_taken`, `l4_typhoon_active`
  - `l3_l4_unified_log`
  - Implements: `specs/integration.md` § State Sharing

### M7.2: Typhoon Scenario Implementation

- [ ] **"Trigger Typhoon Scenario" button**:
  - Fires: Tan Poh Lek fall event (E1) + Nurse Aileen (Caregiver in North zone) cancellation
  - Implements: `specs/L4-care-agent.md` § Typhoon Scenario
- [ ] **Sequential-within-1000ms protocol** (CORRECTED timing):
  ```
  T+0ms:    Typhoon triggered
  T+5ms:     L3 receives cancellation, L4 perceives fall
  T+10ms:    L3 Solver starts re-optimisation
  T+50ms:    L3 Solver returns new schedule
  T+55ms:    L4 reads final L3 schedule
  T+60ms:    L4 Reasoning + Actions execute
  T+100ms:   Both outputs displayed in unified log
  ```

  - Implements: `specs/integration.md` § Coordination Protocol (CORRECTED)

### M7.3: Unified Event Log

- [ ] **Combined log view**: L3 scheduling events + L4 care actions
- [ ] **Filterable**: All | L3 Only | L4 Only | Typhoon
- [ ] **Color coding**: L3 = blue, L4 = orange
- [ ] **Timestamp + source layer + action details**
  - Implements: `specs/L4-care-agent.md` § Unified Event Log

### M7.4: Typhoon Debounce

- [ ] **Disable typhoon button for 5 seconds** after trigger
- [ ] **Show countdown** during debounce period
  - Implements: Decision OD-003

---

## Milestone 8: Sidebar Navigation and App Shell

### M8.1: Navigation

- [ ] **Sidebar navigation** with radio buttons: L1 Fall Detection | L2 Health Risk | L3 Schedule | L4 Care Agent
- [ ] **Page routing**: Show/hide layer content based on selection
- [ ] **Persistent state**: Cross-layer state persists during navigation

### M8.2: App Header

- [ ] **App title**: "AgeCareAI — Autonomous Elder Care Platform"
- [ ] **Subtitle**: "Singapore Elder Care System"
- [ ] **Version display**: "Demo v1.0"

---

## Milestone 9: Decisions Documentation

### M9.1: decisions.md

- [ ] **Create `decisions.md`** alongside `app.py`
- [ ] **Document all 5 approved decisions**:
  1. L1 CNN: sklearn RandomForest with statistical features
  2. L2 SHAP Fallback: Bar chart on failure
  3. L4 Typhoon Debounce: 5 second disable
  4. L4 NEHR Log: Structured JSON
  5. L3 Schedule Priority: Certification over zone
- [ ] **Include rationale** for each decision

---

## Milestone 10: Verification and Testing

### M10.1: Functional Verification

- [ ] **Verify L1**: All 3 sequences classify correctly, fall alert fires at ≥0.85
- [ ] **Verify L2**: All 20 seniors display, risk table sorted correctly, SHAP values show
- [ ] **Verify L3**: Schedule satisfies all constraints, cancel button re-solves <500ms
- [ ] **Verify L4**: All 3 events trigger correct actions, typhoon shows unified log

### M10.2: Integration Verification

- [ ] **Verify typhoon scenario**: L3 re-optimises AND L4 acts within 2 seconds
- [ ] **Verify unified log**: Shows both L3 and L4 entries with correct timestamps
- [ ] **Verify debounce**: Button disabled for 5 seconds after typhoon trigger

### M10.3: NFR Verification

- [ ] **Startup time**: < 10 seconds
- [ ] **L1 inference**: < 100ms per window
- [ ] **L3 initial solve**: < 1000ms
- [ ] **L3 re-solve**: < 500ms
- [ ] **Memory footprint**: < 500MB

---

## Value Rank (Per SPEC § Brief)

### High Priority (Demo Centrepiece)

1. **Typhoon integration** (M7) — The demo centrepiece, must work flawlessly
2. **L3 MILP solver** (M5) — Core scheduling functionality with real-time re-solve
3. **L2 risk dashboard** (M4) — Tele-nurse worklist with SHAP explainability

### Medium Priority

4. **L4 care agent** (M6) — Decision tree with unified event log
5. **L1 fall detection** (M3) — CNN with visual alerts

### Foundation (Must Complete First)

6. **Data models** (M1.2) — All dataclasses and enums
7. **Simulated data** (M2) — Realistic Singapore data for all layers
8. **App shell** (M8) — Navigation and routing

---

## Dependencies

```
M1 (Foundation)
  └── M2 (Data)
        ├── M3 (L1 Fall Detection)
        ├── M4 (L2 Health Risk)
        ├── M5 (L3 Scheduler)
        └── M6 (L4 Care Agent)
              └── M7 (Integration) ← depends on M5 + M6
                    └── M10 (Verification)
```

---

## Spec References

| Spec File                           | Implements       |
| ----------------------------------- | ---------------- |
| `specs/data-models.md`              | M1.2, M2.1, M2.3 |
| `specs/L1-fall-detection.md`        | M3               |
| `specs/L2-health-risk.md`           | M4               |
| `specs/L3-schedule-optimization.md` | M5               |
| `specs/L4-care-agent.md`            | M6               |
| `specs/integration.md`              | M7, M8.1         |
