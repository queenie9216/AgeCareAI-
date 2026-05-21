# AgeCareAI — Autonomous Elder Care Platform

## Project Overview

**Project Name:** AgeCareAI
**Type:** Streamlit Web Application (Single-file Python)
**Context:** Singapore · MGMT 655 Individual Assignment · Week 9

## Core Functionality

Autonomous elder care platform with 4 integrated AI layers serving Singapore's eldercare system.

## Tech Stack

- Python, Streamlit
- XGBoost, SHAP (L2 ML)
- OR-Tools/MILP (L3 optimization)
- scikit-learn, PyTorch (L1 CNN)
- numpy, pandas, plotly
- No external APIs — all data simulated
- No database required

## Layer Specifications

### L1 — Fall Detection (Deep Learning · CNN)

- Simulate wearable accelerometer data stream (3-axis, 50Hz)
- Pre-load 3 sequences: normal walk, shuffle gait, fall event
- Lightweight CNN or transfer-learning-inspired classifier
- Real-time classification with confidence scores
- Visual alert triggered at ≥0.85 fall confidence

### L2 — Health Risk Dashboard (Supervised ML · XGBoost)

- Simulated dataset: 20 seniors
- Features: age, resting HR, SpO2, sleep hours, step count, previous hospitalisations, frailty index
- XGBoost classifier for 30-day readmission risk (low/medium/high)
- Traffic-light table sorted by risk score
- SHAP values for top 3 risk factors per senior
- Use case: tele-nurse worklist

### L3 — Caregiver Schedule Optimiser (MILP · OR-Tools)

- 10 seniors, 5 caregivers
- Senior attributes: care needs, location zones (N/S/E/W/Central)
- Caregiver attributes: certifications, location zones, availability
- Hard constraints: certification match, max 2 seniors/caregiver/day, same-zone preference
- "Caregiver cancels" button → re-solve in real time (milliseconds)

### L4 — Autonomous Care Agent (AI Agent · Perception–Reasoning–Action)

- Monitor simulated event feed
- Pre-loaded events:
  1. Mr Tan, 78: fall confirmed 0.91 confidence, red-risk profile
  2. Mrs Lim, 72: SpO2 dropped to 91%, amber-risk
  3. Mr Ng, 80: missed 2 medication doses, green-risk
- Decision tree logic:
  - Fall + red → EMS + family alert + NEHR log
  - Vitals drop + amber → family alert + polyclinic booking
  - Missed meds + green → reminder only
- Visual display of perception → reasoning → action steps
- "Trigger typhoon scenario" button: Mr Tan falls AND caregiver cancels simultaneously
  - L3 re-optimises AND L4 acts within same second
  - Unified event log showing both responses

### Integration Requirement

Typhoon button on L4 must call L3's solver live and show both outputs (re-optimised schedule + agent action log) updating simultaneously. This is the demo centrepiece.

## Navigation

Single app.py with sidebar navigation between layers.

## COC Requirement

- Pause before implementing each layer
- Ask user for key design decisions
- Log decisions in decisions.md alongside code

## Success Criteria

- Single `streamlit run app.py` execution
- All 4 layers functional and navigable
- Typhoon scenario demonstrates real-time integration
