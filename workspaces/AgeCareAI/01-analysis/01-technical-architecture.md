/btw # AgeCareAI — Technical Architecture Document

**Project:** Autonomous Elder Care Platform
**Version:** 1.0
**Date:** 2026-05-21
**Status:** Analysis Complete

---

## Executive Summary

AgeCareAI is a single-Streamlit web application integrating four AI layers for elder care: (L1) CNN-based fall detection from accelerometer data, (L2) XGBoost health risk scoring with SHAP explainability, (L3) OR-Tools MILP caregiver scheduling, and (L4) autonomous care agent with Perception-Reasoning-Action pattern. The application runs entirely client-side with simulated data, requiring no external APIs or databases.

**Architecture Complexity: Moderate**

- Single-page Streamlit app with four functional layers
- In-process ML models (PyTorch CNN + XGBoost)
- MILP solver for real-time scheduling
- Event-driven inter-layer integration for typhoon scenario

---

## 1. System Architecture Overview

### 1.1 Application Structure

```
app.py                          # Single entry point, Streamlit page config
├── L1_Fall_Detection/          # CNN accelerometer classifier
│   ├── model.py                 # PyTorch lightweight CNN
│   ├── data_generator.py       # 3-axis @ 50Hz accelerometer simulator
│   └── inference.py             # Real-time classification pipeline
├── L2_Health_Dashboard/        # XGBoost risk stratification
│   ├── model.py                 # XGBoost classifier (low/medium/high)
│   ├── shap_explainer.py       # SHAP value computation
│   └── senior_data.py          # 20-senior simulated dataset
├── L3_Caregiver_Schedule/      # MILP optimization
│   ├── optimizer.py             # OR-Tools scheduler
│   ├── constraints.py           # Hard constraint definitions
│   └── rebalance.py             # Real-time re-solve on cancellation
├── L4_Care_Agent/              # Autonomous decision agent
│   ├── perception.py             # Event feed monitoring
│   ├── reasoning.py             # Decision tree logic
│   └── action.py                # Alert/notification dispatcher
└── utils/                      # Shared utilities
    ├── session_state.py        # Streamlit session persistence
    └── plot_helpers.py          # Plotly visualization utilities
```

### 1.2 Technology Stack

| Layer            | Technology              | Purpose                              |
| ---------------- | ----------------------- | ------------------------------------ |
| UI Framework     | Streamlit 1.28+         | Single-page web application          |
| L1 Deep Learning | PyTorch 2.x             | Lightweight CNN for fall detection   |
| L2 ML            | XGBoost 2.x, SHAP 0.45+ | Risk classification + explainability |
| L3 Optimization  | OR-Tools 9.x            | MILP solver for scheduling           |
| Visualization    | Plotly 5.x              | Interactive charts and dashboards    |
| Data             | NumPy, Pandas           | Data manipulation and simulation     |

### 1.3 Data Flow Architecture

```
[Accelerometer Simulation] → [L1 CNN] → [Fall Alert + Confidence]
                                    ↓
[Senior Health Data] → [L2 XGBoost] → [Risk Scores + SHAP] → [Tele-Nurse Worklist]
                                    ↓
[Care Requirements] → [L3 MILP] → [Daily Assignment Schedule]
       ↑                    ↓
[Caregiver Events] → [L4 Agent] → [Reasoning Chain] → [Actions: EMS/Family/Polyclinic]
                                    ↓
                              [Typhoon Scenario: L3 + L4 simultaneous update]
```

---

## 2. L1 — Fall Detection (CNN)

### 2.1 Architecture Pattern

**Pattern:** Temporal Convolutional Neural Network (TCN) / 1D CNN
**Rationale:** Accelerometer data is a 1D time series. 1D CNNs capture local temporal patterns efficiently with fewer parameters than RNNs/LSTMs, making them ideal for lightweight deployment.

### 2.2 Model Architecture

```python
# Lightweight 1D CNN for Accelerometer Classification
class FallDetectionCNN(nn.Module):
    def __init__(self, input_channels=3, sequence_length=150):  # 3 seconds @ 50Hz
        super().__init__()
        # Input: (batch, 3, 150)

        self.conv_block1 = nn.Sequential(
            nn.Conv1d(3, 32, kernel_size=5, stride=2, padding=2),  # → (32, 75)
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2)  # → (32, 37)
        )

        self.conv_block2 = nn.Sequential(
            nn.Conv1d(32, 64, kernel_size=3, stride=1, padding=1),  # → (64, 37)
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2)  # → (64, 18)
        )

        self.conv_block3 = nn.Sequential(
            nn.Conv1d(64, 64, kernel_size=3, stride=1, padding=1),  # → (64, 18)
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1)  # → (64, 1)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 3)  # 3 classes: normal, shuffle, fall
        )

    def forward(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.conv_block3(x)
        x = self.classifier(x)
        return x
```

**Parameter Count:** ~25,000 parameters (extremely lightweight)
**Inference Speed:** <5ms on CPU

### 2.3 Input Data Specification

| Parameter       | Value                              |
| --------------- | ---------------------------------- |
| Sampling Rate   | 50 Hz                              |
| Axis            | X, Y, Z (3-channel)                |
| Sequence Length | 150 samples (3 seconds)            |
| Data Range      | -4g to +4g (normalized)            |
| Preprocessing   | Mean subtraction, L2 normalization |

### 2.4 Pre-loaded Sequences

| Sequence       | Description                                             | Label   | Confidence (target) |
| -------------- | ------------------------------------------------------- | ------- | ------------------- |
| `normal_walk`  | Regular walking pattern, periodic vertical oscillation  | Normal  | 0.95                |
| `shuffle_gait` | Reduced stride length, increased lateral sway           | Shuffle | 0.87                |
| `fall_event`   | Rapid deceleration + impact spike + post-fall stillness | Fall    | 0.91                |

### 2.5 Alert Threshold Logic

```python
def check_fall_alert(confidence: float, threshold: float = 0.85) -> bool:
    """Trigger visual alert when fall confidence exceeds threshold."""
    return confidence >= threshold

# Streamlit callback integration
def on_prediction(prediction: str, confidence: float):
    if prediction == "fall" and check_fall_alert(confidence):
        st.error(f"FALL DETECTED — Confidence: {confidence:.2%}")
```

### 2.6 Training Configuration

```python
training_config = {
    "optimizer": "Adam",
    "learning_rate": 0.001,
    "epochs": 50,
    "batch_size": 32,
    "loss": nn.CrossEntropyLoss(),
    "scheduler": torch.optim.lr_scheduler.ReduceLROnPlateau,
}
```

---

## 3. L2 — Health Risk Dashboard (XGBoost + SHAP)

### 3.1 Architecture Pattern

**Pattern:** Gradient Boosted Decision Trees (XGBoost) for Multi-Class Classification
**Rationale:** XGBoost provides excellent accuracy on tabular data with built-in feature importance. SHAP values offer game-theoretic explainability essential for healthcare decision support.

### 3.2 Senior Dataset Schema

```python
@dataclass
class Senior:
    id: int
    name: str
    age: int                          # Range: 65-90
    resting_hr: int                   # Range: 55-100 bpm
    spo2: float                       # Range: 88-100%
    sleep_hours: float                # Range: 4-10 hours
    step_count: int                   # Range: 500-15000 steps/day
    prev_hospitalizations: int       # Range: 0-8
    frailty_index: float              # Range: 0.0-1.0 (higher = more frail)
    risk_level: str                   # "low", "medium", "high" (target)
```

### 3.3 Feature Engineering

```python
features = [
    "age",
    "resting_hr",
    "spo2",
    "sleep_hours",
    "step_count",
    "prev_hospitalizations",
    "frailty_index",
]

# Derived features
derived_features = [
    "hr_z_score",          # (hr - population_mean) / population_std
    "spo2_deficit",        # 100 - spo2 (larger = worse)
    "activity_ratio",       # step_count / age-adjusted_baseline
    "frailty_hr_interaction",  # frailty_index * resting_hr
]
```

### 3.4 XGBoost Model Configuration

```python
xgb_params = {
    "objective": "multi:softprob",
    "num_class": 3,
    "max_depth": 4,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "min_child_weight": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "tree_method": "hist",  # Fast histogram-based algorithm
}

# Class mapping
class_mapping = {0: "low", 1: "medium", 2: "high"}
```

### 3.5 SHAP Integration

```python
import shap

def compute_shap_values(model, X: pd.DataFrame, senior_id: int) -> dict:
    """Compute SHAP values for a specific senior."""
    explainer = shap.TreeExplainer(model)
    senior_idx = X["id"] == senior_id
    shap_values = explainer.shap_values(X[senior_idx])

    return {
        "values": shap_values[0],  # 3-class SHAP values
        "base_value": explainer.expected_value,
        "feature_importance": dict(zip(features, abs(shap_values[0]).mean(axis=0)))
    }

def get_top_3_factors(shap_result: dict) -> list:
    """Extract top 3 risk factors for display."""
    importance = shap_result["feature_importance"]
    sorted_factors = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
    return sorted_factors[:3]
```

### 3.6 Traffic Light Visualization

```python
def get_risk_color(risk_level: str) -> str:
    """Return hex color for risk level."""
    return {
        "low": "#22c55e",    # Green
        "medium": "#f59e0b", # Amber
        "high": "#ef4444"    # Red
    }.get(risk_level, "#6b7280")

def render_risk_table(seniors: list[Senior], shap_results: dict) -> None:
    """Render Plotly table with traffic light colors."""
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["Name", "Age", "Risk Level", "Top Factors"],
            fill_color="#1f2937",
            font_color="white"
        ),
        cells=dict(
            values=[
                [s.name for s in seniors],
                [s.age for s in seniors],
                [s.risk_level for s in seniors],
                [get_top_3_factors(shap_results[s.id]) for s in seniors],
            ],
            fill_color=[[get_risk_color(s.risk_level) for s in seniors]] * 4,
        )
    )])
    st.plotly_chart(fig)
```

---

## 4. L3 — Caregiver Schedule Optimizer (OR-Tools MILP)

### 4.1 Architecture Pattern

**Pattern:** Mixed Integer Linear Programming (MILP) with OR-Tools CP-SAT Solver
**Rationale:** Caregiver scheduling is a classic constraint satisfaction and optimization problem. MILP provides optimal solutions with configurable hard/soft constraints, and CP-SAT offers millisecond-level solve times for this problem scale.

### 4.2 Problem Formulation

**Decision Variables:**

```python
# x[i,j] = 1 if caregiver i is assigned to senior j on given day
x = {(i, j): model.NewBoolVar(f"assign_{i}_{j}") for i in caregivers for j in seniors}

# y[i] = 1 if caregiver i is available (for re-solve scenarios)
y = {i: model.NewBoolVar(f"available_{i}") for i in caregivers}
```

### 4.3 Data Model

```python
@dataclass
class Senior:
    id: int
    name: str
    care_needs: list[str]      # e.g., ["dementia", "mobility", "diabetes"]
    zone: str                  # "N", "S", "E", "W", "Central"

@dataclass
class Caregiver:
    id: int
    name: str
    certifications: list[str]  # e.g., ["dementia", "medication", "physio"]
    zone: str                  # "N", "S", "E", "W", "Central"
    available_days: list[int]  # 0=Monday, 6=Sunday
```

### 4.4 Constraint Definitions

```python
def add_constraints(model, x, caregivers, seniors, params):
    # Constraint 1: Certification Match (HARD)
    # Caregiver must have certification for each senior's care need
    for s in seniors:
        for c in caregivers:
            required_certs = set(s.care_needs)
            caregiver_certs = set(c.certifications)
            if not required_certs.issubset(caregiver_certs):
                model.Add(x[(c.id, s.id)] == 0)

    # Constraint 2: Max 2 Seniors Per Caregiver Per Day (HARD)
    for c in caregivers:
        for day in range(7):
            assigned = [x[(c.id, s.id)] for s in seniors if day in s.availability]
            model.Add(sum(assigned) <= params["max_seniors_per_caregiver"])

    # Constraint 3: Same-Zone Preference (SOFT - penalized)
    # Encoded as objective function penalty, not hard constraint
    for c in caregivers:
        for s in seniors:
            if c.zone != s.zone:
                model.Add(x[(c.id, s.id)] == 0).OnlyEnforceIf(
                    model.NewConstant(params["zone_strict"])  # Zone strict mode
                )

    # Constraint 4: Each Senior Gets At Most One Caregiver Per Day (HARD)
    for s in seniors:
        for day in range(7):
            assigned = [x[(c.id, s.id)] for c in caregivers]
            model.Add(sum(assigned) <= 1)
```

### 4.5 Objective Function

```python
def objective_function(model, x, caregivers, seniors, params):
    # Maximize assignments while penalizing zone mismatches
    total_assignments = sum(x[(c.id, s.id)] for c in caregivers for s in seniors)

    # Soft penalty for cross-zone assignments
    zone_penalty = sum(
        x[(c.id, s.id)] * params["zone_penalty"]
        for c in caregivers
        for s in seniors
        if c.zone != s.zone
    )

    return total_assignments - zone_penalty
```

### 4.6 Re-solve on Caregiver Cancellation

```python
def rebalance_on_cancellation(caregiver_id: int, model, x, solver, params):
    """Real-time re-solve when a caregiver cancels."""
    # Mark caregiver as unavailable
    for s in seniors:
        model.Add(x[(caregiver_id, s.id)] == 0)

    # Re-solve with same constraints
    solver.Solve(model)

    return extract_solution(solver, x)
```

**Solve Time Target:** <100ms for 10 seniors, 5 caregivers

### 4.7 Schedule Visualization

```python
def render_schedule(schedule: dict, caregivers: list, seniors: list) -> None:
    """Render weekly schedule as a Gantt-style chart."""
    import plotly.figure_factory as ff

    df = []
    for (caregiver_id, senior_id, day), assigned in schedule.items():
        if assigned:
            caregiver = next(c for c in caregivers if c.id == caregiver_id)
            senior = next(s for s in seniors if s.id == senior_id)
            df.append(dict(
                Task=caregiver.name,
                Start=day,
                Finish=day + 1,
                Resource=senior.name
            ))

    fig = ff.create_gantt(df, index_col="Resource", show_colorbar=True)
    st.plotly_chart(fig)
```

---

## 5. L4 — Autonomous Care Agent (Perception-Reasoning-Action)

### 5.1 Architecture Pattern

**Pattern:** Perception-Reasoning-Action (PRA) Cognitive Architecture
**Rationale:** Healthcare decision support requires transparent, auditable reasoning chains. PRA provides clear traceability from perception (event detection) through reasoning (decision logic) to action (alerts, escalations).

### 5.2 Component Architecture

```python
class CareAgent:
    def __init__(self):
        self.event_buffer = []
        self.decision_history = []

    def perceive(self, event: Event) -> PerceivedEvent:
        """Process raw event into structured perception."""
        # Classify event type
        # Extract relevant context (senior profile, risk level)
        # Compute urgency score
        pass

    def reason(self, perception: PerceivedEvent) -> ReasoningResult:
        """Apply decision tree to perception."""
        # Traverse decision tree
        # Generate action recommendations
        # Compute confidence
        pass

    def act(self, reasoning: ReasoningResult) -> list[Action]:
        """Execute recommended actions."""
        # Dispatch alerts
        # Log to NEHR
        # Trigger L3 re-optimization if needed
        pass
```

### 5.3 Event Schema

```python
@dataclass
class Event:
    event_id: str
    senior_id: int
    event_type: str          # "fall", "vitals_drop", "medication_missed"
    timestamp: datetime
    raw_data: dict           # Type-specific payload
    confidence: float        # Sensor/model confidence

@dataclass
class PerceivedEvent:
    event: Event
    senior: Senior           # Enriched context
    urgency_score: float      # 0.0 - 1.0
    category: str            # "emergency", "warning", "info"
```

### 5.4 Decision Tree Logic

```python
DECISION_TREE = {
    ("fall", "high"): {
        "actions": ["ems_alert", "family_alert", "nehr_log"],
        "priority": 1,
        "response_time": "immediate",
    },
    ("fall", "medium"): {
        "actions": ["family_alert", "polyclinic_booking", "nehr_log"],
        "priority": 2,
        "response_time": "within_1_hour",
    },
    ("fall", "low"): {
        "actions": ["family_alert", "nehr_log"],
        "priority": 3,
        "response_time": "within_4_hours",
    },
    ("vitals_drop", "high"): {
        "actions": ["ems_alert", "family_alert", "nehr_log"],
        "priority": 1,
        "response_time": "immediate",
    },
    ("vitals_drop", "medium"): {
        "actions": ["family_alert", "polyclinic_booking"],
        "priority": 2,
        "response_time": "within_1_hour",
    },
    ("medication_missed", _): {
        "actions": ["reminder"],
        "priority": 4,
        "response_time": "within_day",
    },
}

def traverse_decision_tree(perception: PerceivedEvent) -> ReasoningResult:
    """Traverse decision tree and return recommended actions."""
    event_type = perception.event.event_type
    risk_level = perception.senior.risk_level

    # Handle wildcard
    if risk_level == "low" and event_type == "vitals_drop":
        risk_key = "medium"  # Vitals drop always elevated
    else:
        risk_key = risk_level

    rule = DECISION_TREE.get((event_type, risk_key), DECISION_TREE[(event_type, "_")])

    return ReasoningResult(
        event_id=perception.event.event_id,
        senior_id=perception.senior.id,
        rule_applied=rule,
        recommended_actions=rule["actions"],
        reasoning_chain=build_reasoning_chain(perception, rule),
    )
```

### 5.5 Pre-loaded Events

| Senior  | Age | Event Type        | Details             | Risk Profile | Confidence |
| ------- | --- | ----------------- | ------------------- | ------------ | ---------- |
| Mr Tan  | 78  | Fall Confirmed    | CNN confidence 0.91 | high         | 0.91       |
| Mrs Lim | 72  | SpO2 Drop         | SpO2 dropped to 91% | medium       | N/A        |
| Mr Ng   | 80  | Medication Missed | Missed 2 doses      | low          | N/A        |

### 5.6 Action Implementation

```python
@dataclass
class Action:
    action_type: str
    target: str
    payload: dict
    timestamp: datetime
    status: str  # "pending", "sent", "failed"

class ActionDispatcher:
    def dispatch_ems_alert(self, senior: Senior, event: Event) -> Action:
        """Send EMS alert with senior location and condition."""
        return Action(
            action_type="ems_alert",
            target="Singapore Civil Defence Force",
            payload={
                "senior_name": senior.name,
                "location": senior.address,
                "condition": event.event_type,
                "timestamp": event.timestamp,
            },
            timestamp=datetime.now(),
            status="sent"
        )

    def dispatch_family_alert(self, senior: Senior, message: str) -> Action:
        """Send SMS/notification to family contact."""
        return Action(
            action_type="family_alert",
            target=senior.emergency_contact,
            payload={"message": message},
            timestamp=datetime.now(),
            status="sent"
        )

    def log_nehr(self, senior: Senior, event: Event, actions: list[Action]) -> Action:
        """Log event and actions to National Electronic Health Record."""
        return Action(
            action_type="nehr_log",
            target="NEHR System",
            payload={
                "nric": senior.nric,
                "event": event.to_dict(),
                "actions_taken": [a.to_dict() for a in actions],
            },
            timestamp=datetime.now(),
            status="sent"
        )
```

---

## 6. Typhoon Scenario Integration

### 6.1 Scenario Definition

**Trigger Conditions:**

1. Mr Tan (high-risk) fall detected (L1)
2. Mr Tan's assigned caregiver cancels (L3)

**Expected Outcome:**

- L3: Real-time re-optimization of Mr Tan's care
- L4: Parallel reasoning and action execution for emergency response
- Unified event log showing both L3 and L4 responses within same second

### 6.2 Implementation Pattern

```python
class TyphoonScenario:
    def __init__(self, l3_scheduler, l4_agent):
        self.l3 = l3_scheduler
        self.l4 = l4_agent

    def trigger(self) -> TyphoonResult:
        """Execute typhoon scenario with parallel L3/L4 response."""
        import concurrent.futures
        from threading import Thread

        result = TyphoonResult()

        # Parallel execution of L3 and L4
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # L3: Re-optimize schedule
            l3_future = executor.submit(self.l3.rebalance_on_cancellation, tan_caregiver_id)

            # L4: Execute emergency response for Mr Tan
            l4_future = executor.submit(self.l4.handle_fall_emergency, tan_senior_id)

            # Collect results
            result.l3_schedule = l3_future.result()
            result.l4_actions = l4_future.result()

        result.unified_log = self.build_unified_log(result)
        return result
```

### 6.3 Streamlit Real-Time Display

```python
def display_typhoon_result(result: TyphoonResult):
    """Display typhoon scenario result with real-time updates."""

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("L3: Schedule Re-optimization")
        render_schedule(result.l3_schedule)

    with col2:
        st.subheader("L4: Emergency Response")
        render_action_log(result.l4_actions)

    # Unified timeline
    st.subheader("Unified Event Timeline")
    render_timeline(result.unified_log)

    # Auto-refresh placeholder for real-time simulation
    placeholder = st.empty()
    with placeholder.container():
        st.info("All updates completed within 1 second")
```

### 6.4 Callback Integration

```python
# Streamlit button callbacks
if st.button("Trigger Typhoon Scenario"):
    result = typhoon.trigger()

    # Display with animation
    with st.spinner("L3 optimizing schedule..."):
        time.sleep(0.3)
    with st.spinner("L4 executing response..."):
        time.sleep(0.3)

    display_typhoon_result(result)
```

---

## 7. Real-Time UI Updates in Streamlit

### 7.1 Patterns for Live Updates

**Pattern 1: Session State with Callbacks**

```python
if "predictions" not in st.session_state:
    st.session_state.predictions = []

def on_new_prediction(pred):
    st.session_state.predictions.append(pred)
    st.rerun()
```

**Pattern 2: Placeholder with Dynamic Content**

```python
status_placeholder = st.empty()
with status_placeholder.container():
    st.info("Processing...")

# After processing
with status_placeholder.container():
    st.success("Complete!")
```

**Pattern 3: Auto-Refresh with Polling**

```python
while True:
    if check_completion():
        st.rerun()
        break
    time.sleep(0.1)  # 100ms polling
```

### 7.2 st.session_state for Cross-Layer State

```python
# Initialize session state
if "l1_predictions" not in st.session_state:
    st.session_state.l1_predictions = []

if "l2_risks" not in st.session_state:
    st.session_state.l2_risks = {}

if "l3_schedule" not in st.session_state:
    st.session_state.l3_schedule = {}

if "l4_actions" not in st.session_state:
    st.session_state.l4_actions = []

if "typhoon_active" not in st.session_state:
    st.session_state.typhoon_active = False
```

### 7.3 Fragment-Level Rerun (Streamlit 1.28+)

```python
from streamlit.runtime.scriptrunner import get_script_run_ctx

@st.fragment
def live_prediction_display():
    """Fragment that reruns independently for live updates."""
    if st.session_state.l1_predictions:
        latest = st.session_state.l1_predictions[-1]
        st.metric("Latest Fall Confidence", f"{latest['confidence']:.2%}")
        if latest["prediction"] == "fall":
            st.error("FALL ALERT")
```

---

## 8. Data Simulation Strategies

### 8.1 L1 Accelerometer Data Generation

```python
class AccelerometerSimulator:
    def __init__(self, sampling_rate=50):
        self.sampling_rate = sampling_rate
        self.sequence_length = 150  # 3 seconds

    def generate_normal_walk(self) -> np.ndarray:
        """Generate 3-second normal walking pattern."""
        t = np.linspace(0, 3, self.sequence_length)
        # X: lateral sway (0.3g, 2Hz)
        x = 0.3 * np.sin(2 * np.pi * 2 * t)
        # Y: forward motion (0.5g, 1.5Hz)
        y = 0.5 * np.sin(2 * np.pi * 1.5 * t)
        # Z: vertical oscillation (1.0g baseline + 0.4g, 3Hz)
        z = 1.0 + 0.4 * np.sin(2 * np.pi * 3 * t)
        return np.stack([x, y, z], axis=0)

    def generate_shuffle_gait(self) -> np.ndarray:
        """Generate shuffle gait pattern (reduced amplitude, irregular)."""
        t = np.linspace(0, 3, self.sequence_length)
        # Reduced vertical oscillation
        z = 1.0 + 0.15 * np.sin(2 * np.pi * 1.5 * t + np.random.randn() * 0.5)
        # Increased lateral sway
        x = 0.5 * np.sin(2 * np.pi * 0.8 * t)
        y = 0.2 * np.sin(2 * np.pi * 0.5 * t)
        return np.stack([x, y, z], axis=0)

    def generate_fall(self) -> np.ndarray:
        """Generate fall event pattern."""
        t = np.linspace(0, 3, self.sequence_length)
        # Pre-fall: normal activity
        pre_fall = np.where(t < 1.0,
            np.stack([
                0.2 * np.sin(2 * np.pi * 1 * t[:50]),
                0.3 * np.sin(2 * np.pi * 1.5 * t[:50]),
                1.0 + 0.2 * np.sin(2 * np.pi * 2 * t[:50])
            ], axis=1),
            np.zeros((50, 3))
        )
        # Fall: rapid deceleration
        fall_idx = slice(50, 75)
        fall_t = (t[fall_idx] - 1.0) * 10
        fall = np.stack([
            -0.5 * fall_t,
            -0.3 * fall_t,
            1.0 - 2.0 * fall_t
        ], axis=1)
        # Impact: spike
        impact = np.array([[2.5, 1.8, 0.2]] * 10)
        # Post-fall: stillness
        post_fall = np.array([[0.1, 0.1, 0.8]] * 65)
        return np.concatenate([pre_fall, fall, impact, post_fall], axis=0).T
```

### 8.2 L2 Senior Data Generation

```python
def generate_senior_dataset(n_seniors=20, seed=42) -> pd.DataFrame:
    """Generate realistic senior health dataset."""
    np.random.seed(seed)

    names = [
        "Tan Ah Lian", "Lim Poh Geok", "Ng Cheng Hock", "Tan Siew Ming",
        "Lee Mei Hua", "Chua Kim Lian", "Ng Huat Seng", "Tan Bok Kwang",
        "Lim Hua Chong", "Lee Siok Koon", "Chua Chee Keong", "Tan Sok Khim",
        "Ng Eng Hua", "Lee Kwok Wai", "Lim Geok Choo", "Tan Chee Seng",
        "Chua Poh Choo", "Lee Jit Meng", "Tan Soo Kim", "Ng Kim Huat"
    ]

    seniors = []
    for i in range(n_seniors):
        age = np.random.randint(65, 91)
        base_risk = compute_base_risk(age)  # Higher age = higher base risk

        senior = {
            "id": i + 1,
            "name": names[i],
            "age": age,
            "resting_hr": np.random.randint(55, 101),
            "spo2": np.random.uniform(88, 100),
            "sleep_hours": np.random.uniform(4, 10),
            "step_count": np.random.randint(500, 15001),
            "prev_hospitalizations": np.random.randint(0, 9),
            "frailty_index": np.clip(base_risk + np.random.uniform(-0.1, 0.1), 0, 1),
        }
        seniors.append(senior)

    df = pd.DataFrame(seniors)
    # Assign risk levels based on composite score
    df["risk_score"] = compute_risk_score(df)
    df["risk_level"] = pd.cut(df["risk_score"],
                               bins=[-np.inf, 0.3, 0.6, np.inf],
                               labels=["low", "medium", "high"])
    return df
```

### 8.3 L3 Schedule Data

```python
# Pre-defined caregiver roster
CAREGIVERS = [
    Caregiver(1, "Nurse Aileen", ["dementia", "medication"], "Central", [0,1,2,3,4]),
    Caregiver(2, "Nurse Bakri", ["mobility", "physio"], "East", [0,1,2,3,4]),
    Caregiver(3, "Nurse Chandra", ["dementia", "medication", "diabetes"], "North", [1,2,3,4,5]),
    Caregiver(4, "Nurse Diana", ["diabetes", "wound_care"], "West", [0,1,2,3,4]),
    Caregiver(5, "Nurse Edwin", ["mobility", "dementia"], "South", [0,1,2,4,5]),
]

# Pre-defined senior assignments
SENIORS = [
    Senior(1, "Mr Tan", ["dementia", "mobility"], "North", [1,3,5]),
    Senior(2, "Mrs Lim", ["diabetes"], "East", [2,4]),
    Senior(3, "Mr Ng", ["medication"], "Central", [1,2,3]),
    # ... 10 seniors total
]
```

---

## 9. File Structure

```
AgeCareAI/
├── app.py                          # Streamlit entry point
├── requirements.txt                # pip dependencies
├── L1/
│   ├── __init__.py
│   ├── fall_cnn.py                 # PyTorch CNN model
│   ├── accelerometer_sim.py       # Data generation
│   └── inference.py               # Real-time inference
├── L2/
│   ├── __init__.py
│   ├── xgboost_model.py            # XGBoost classifier
│   ├── senior_data.py              # Dataset generation
│   └── shap_explainer.py          # SHAP integration
├── L3/
│   ├── __init__.py
│   ├── optimizer.py                # OR-Tools MILP
│   ├── constraints.py              # Constraint definitions
│   └── scheduler.py                # Schedule visualization
├── L4/
│   ├── __init__.py
│   ├── agent.py                    # Care agent
│   ├── perception.py              # Event processing
│   ├── reasoning.py               # Decision tree
│   └── actions.py                 # Alert dispatch
└── utils/
    ├── __init__.py
    ├── session_state.py            # Streamlit state
    └── plot_helpers.py             # Plotly utilities
```

---

## 10. Dependencies

```
# requirements.txt
streamlit>=1.28.0
torch>=2.0.0
xgboost>=2.0.0
shap>=0.45.0
ortools>=9.0.0
numpy>=1.24.0
pandas>=2.0.0
plotly>=5.18.0
```

---

## 11. Implementation Phases

### Phase 1: Foundation

- Set up Streamlit app with sidebar navigation
- Implement L1 accelerometer simulation and CNN model
- Verify fall detection pipeline with pre-loaded sequences

### Phase 2: Risk Stratification

- Implement senior dataset generation
- Train XGBoost model on risk classification
- Integrate SHAP explainability
- Build L2 dashboard with traffic-light table

### Phase 3: Schedule Optimization

- Implement OR-Tools MILP solver
- Define constraint definitions
- Build schedule visualization
- Implement caregiver cancellation re-solve

### Phase 4: Autonomous Agent

- Implement Perception-Reasoning-Action loop
- Build decision tree with pre-loaded events
- Implement action dispatcher
- Build event log display

### Phase 5: Integration

- Implement typhoon scenario (L3 + L4 simultaneous)
- Add unified event timeline
- Polish UI/UX
- End-to-end testing

---

## 12. Risk Assessment

| Risk                             | Likelihood | Impact | Mitigation                                       |
| -------------------------------- | ---------- | ------ | ------------------------------------------------ |
| CNN model too slow for real-time | Low        | Medium | Use lightweight architecture; pre-loaded weights |
| MILP solve timeout               | Low        | Medium | Limit problem size; use CP-SAT solver            |
| SHAP computation bottleneck      | Low        | Low    | Pre-compute during dataset generation            |
| Streamlit state leakage          | Medium     | Low    | Use explicit session state management            |
| Typhoon scenario race condition  | Low        | High   | Use ThreadPoolExecutor for atomic result         |

---

## 13. Success Criteria

- [ ] `streamlit run app.py` launches single-page application
- [ ] Sidebar navigation switches between all 4 layers
- [ ] L1 displays accelerometer waveforms and fall classification with confidence
- [ ] L1 triggers visual alert at >=0.85 fall confidence
- [ ] L2 displays traffic-light table for 20 seniors sorted by risk
- [ ] L2 shows SHAP values for top 3 risk factors per senior
- [ ] L3 generates valid schedule meeting all hard constraints
- [ ] L3 re-solves in <100ms on caregiver cancellation
- [ ] L4 decision tree maps events to correct actions
- [ ] L4 displays perception -> reasoning -> action chain
- [ ] Typhoon button triggers simultaneous L3 + L4 updates
- [ ] Unified event log shows responses within 1 second

---

## Appendix A: Model Card — Fall Detection CNN

| Attribute       | Value                                                      |
| --------------- | ---------------------------------------------------------- |
| Model Type      | 1D Convolutional Neural Network                            |
| Input           | 3-channel time series (X, Y, Z accelerometer), 150 samples |
| Output          | 3-class softmax (Normal, Shuffle, Fall)                    |
| Parameters      | ~25,000                                                    |
| Inference Time  | <5ms (CPU)                                                 |
| Training Data   | Simulated accelerometer sequences                          |
| Alert Threshold | 0.85 confidence                                            |

## Appendix B: Model Card — Health Risk XGBoost

| Attribute      | Value                            |
| -------------- | -------------------------------- |
| Model Type     | Gradient Boosted Decision Trees  |
| Input          | 7 features per senior            |
| Output         | 3-class (Low, Medium, High risk) |
| Estimators     | 100                              |
| Max Depth      | 4                                |
| Explainability | SHAP TreeExplainer               |

## Appendix C: SHAP Integration for Tele-Nurse Worklist

The tele-nurse worklist use case requires:

1. Senior list sorted by descending risk score
2. Color-coded risk indicators (traffic light)
3. Top 3 contributing factors per senior (SHAP)
4. Recommended action based on risk level

```python
def build_tele_nurse_worklist(seniors: list, shap_results: dict) -> pd.DataFrame:
    """Build worklist for tele-nurse use case."""
    rows = []
    for senior in sorted(seniors, key=lambda s: s.risk_score, reverse=True):
        top_factors = get_top_3_factors(shap_results[senior.id])
        rows.append({
            "Name": senior.name,
            "Risk": senior.risk_level.upper(),
            "Risk Color": get_risk_color(senior.risk_level),
            "Top Factors": ", ".join([f[0] for f in top_factors]),
            "Action": get_recommended_action(senior.risk_level),
        })
    return pd.DataFrame(rows)
```
