# Todo: M1.1 + M1.2 + M8 — Foundation and App Shell

## Status: IN PROGRESS

## Implementation Details

### 1. requirements.txt

Create with: streamlit, xgboost, shap, ortools, scikit-learn, numpy, pandas, plotly

### 2. app.py Structure

- Streamlit page config (title, layout)
- Sidebar navigation (radio buttons for L1-L4)
- Session state initialization
- Layer routing (show/hide based on selection)

### 3. Data Models

- Zone enum: NORTH, SOUTH, EAST, WEST, CENTRAL
- Day enum: MON, TUE, WED, THU, FRI
- EventType enum: FALL, VITALS, MEDICATION
- RiskBand enum: RED, AMBER, GREEN
- RiskLevel enum: LOW, MEDIUM, HIGH
- Senior dataclass
- SeniorFeatures dataclass
- Caregiver dataclass
- Event dataclass
- SHAPFactor dataclass
- ScheduleAssignment dataclass
- SeniorAssignment dataclass

## Verification

- [ ] requirements.txt created with all dependencies
- [ ] app.py runs with `streamlit run app.py`
- [ ] Sidebar navigation works
- [ ] Data models import without errors
