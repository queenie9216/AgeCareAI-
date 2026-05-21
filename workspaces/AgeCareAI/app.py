"""
AgeCareAI — Autonomous Elder Care Platform
Singapore

A Streamlit application with 4 integrated AI layers:
- L1: Fall Detection (RandomForest CNN)
- L2: Health Risk Dashboard (XGBoost + SHAP)
- L3: Caregiver Schedule Optimiser (OR-Tools MILP)
- L4: Autonomous Care Agent (Perception-Reasoning-Action)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import time

# =============================================================================
# DATA MODELS & ENUMS
# =============================================================================

class Zone(Enum):
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    CENTRAL = "Central"

class Day(Enum):
    MON = "Monday"
    TUE = "Tuesday"
    WED = "Wednesday"
    THU = "Thursday"
    FRI = "Friday"

class EventType(Enum):
    FALL = "Fall Detected"
    SPO2_DROP = "SpO2 Drop"
    MISSED_MEDS = "Missed Medication"

class RiskBand(Enum):
    RED = "Red"
    AMBER = "Amber"
    GREEN = "Green"

class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

@dataclass
class SeniorFeatures:
    """Health features for a senior citizen."""
    age: int
    resting_hr: int
    spo2: int
    sleep_hours: float
    step_count: int
    prev_hospitalisations: int
    frailty_index: float

@dataclass
class Senior:
    """Senior citizen entity."""
    id: str
    name: str
    age: int
    zone: Zone
    care_needs: List[str]
    care_hours: float
    features: SeniorFeatures
    family_contact: str = "+65 9999 9999"
    risk_band: RiskBand = RiskBand.GREEN

@dataclass
class Caregiver:
    """Caregiver entity."""
    id: str
    name: str
    certifications: List[str]
    home_zone: Zone
    availability: List[Day]
    max_seniors_per_day: int = 2
    active: bool = True
    assigned_seniors: List[str] = field(default_factory=list)

@dataclass
class Event:
    """Care event entity."""
    id: str
    senior_id: str
    senior_name: str
    senior_age: int
    event_type: EventType
    timestamp: datetime
    risk_band: RiskBand
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    actions_taken: List[str] = field(default_factory=list)

@dataclass
class SHAPFactor:
    """SHAP explanation factor."""
    feature_name: str
    feature_value: float
    shap_value: float
    direction: str  # "increases_risk" or "decreases_risk"

@dataclass
class RiskAssessment:
    """Risk assessment result."""
    senior_id: str
    senior_name: str
    risk_level: RiskLevel
    risk_score: float
    probabilities: Dict[str, float]
    top_3_factors: List[SHAPFactor]

@dataclass
class SeniorAssignment:
    """Assignment of a senior to a caregiver slot."""
    senior_id: str
    senior_name: str
    zone: Zone
    care_needs: List[str]
    zone_match: bool

@dataclass
class ScheduleAssignment:
    """Schedule assignment for a caregiver."""
    caregiver_id: str
    caregiver_name: str
    day: Day
    slots: List[SeniorAssignment]
    zone_match_count: int = 0

@dataclass
class LogEntry:
    """Unified log entry for typhoon scenario."""
    timestamp: datetime
    source: str  # "L3" or "L4"
    event_type: str
    details: Dict[str, Any]
    correlation_id: Optional[str] = None

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    """Initialize all session state variables."""
    if 'current_layer' not in st.session_state:
        st.session_state.current_layer = "L1"

    # L1 State
    if 'l1_current_sequence' not in st.session_state:
        st.session_state.l1_current_sequence = "Normal Walk"
    if 'l1_classification_log' not in st.session_state:
        st.session_state.l1_classification_log = []
    if 'l1_alert_triggered' not in st.session_state:
        st.session_state.l1_alert_triggered = False

    # L2 State
    if 'l2_seniors_df' not in st.session_state:
        st.session_state.l2_seniors_df = None
    if 'l2_risk_predictions' not in st.session_state:
        st.session_state.l2_risk_predictions = {}
    if 'l2_shaps' not in st.session_state:
        st.session_state.l2_shaps = {}
    if 'l2_assessments' not in st.session_state:
        st.session_state.l2_assessments = []

    # L3 State
    if 'l3_schedule' not in st.session_state:
        st.session_state.l3_schedule = []
    if 'l3_active_caregivers' not in st.session_state:
        st.session_state.l3_active_caregivers = []
    if 'l3_solve_time_ms' not in st.session_state:
        st.session_state.l3_solve_time_ms = 0.0

    # L4 State
    if 'l4_event_log' not in st.session_state:
        st.session_state.l4_event_log = []
    if 'l4_actions_taken' not in st.session_state:
        st.session_state.l4_actions_taken = {}
    if 'l4_typhoon_active' not in st.session_state:
        st.session_state.l4_typhoon_active = False
    if 'l4_typhoon_countdown' not in st.session_state:
        st.session_state.l4_typhoon_countdown = 0

    # Cross-layer unified log
    if 'l3_l4_unified_log' not in st.session_state:
        st.session_state.l3_l4_unified_log = []

# =============================================================================
# DATA GENERATION
# =============================================================================

def generate_singapore_seniors() -> List[Senior]:
    """Generate 20 seniors with realistic Singapore demographics."""
    chinese_names = ["Tan Poh Lek", "Lee Siu Ming", "Lim Choon Huat", "Ng Teck Seng",
                     "Wong Kam Seng", "Chen Yoke Lan", "Goh Kwee Chuan", "Koh Mui Huang",
                     "Teo Ah Kiang", "Ang Bee Lian", "Tan Wei Jie", "Lee Pei Ling"]
    malay_names = ["Abdul Rahim", "Fatimah Binte Ahmad", "Rahim Bin Hassan", "Aminah Binte Dollah",
                   "Ibrahim Bin Ahmad", "Zainab Binte Muhammad", "Syed Azizi", "Norhaliza Binte Jamal"]
    indian_names = ["Nair Subramaniam", "Patel Ravi Kumar", "Singh Harjeet", "Raman Menon",
                    "Kumari d/o Gopal", "Chettiar Murugan", "Bhatia Suresh", "Mohammed Faizal"]

    seniors = []
    all_names = chinese_names + malay_names + indian_names

    # Clinical rules for risk labels
    risk_data = [
        # (name, age, zone, care_needs, features, family_contact)
        ("Tan Poh Lek", 78, Zone.NORTH, ["Dementia", "Mobility Support"], SeniorFeatures(78, 72, 97, 5.5, 1200, 3, 0.65), "+65 9123 4567", RiskBand.RED),
        ("Lim Sok Kuan", 72, Zone.SOUTH, ["Chronic Disease"], SeniorFeatures(72, 85, 91, 6.0, 2500, 2, 0.45), "+65 9234 5678", RiskBand.AMBER),
        ("Ng Teck Seng", 80, Zone.EAST, ["Companion"], SeniorFeatures(80, 68, 98, 7.0, 3000, 1, 0.30), "+65 9345 6789", RiskBand.GREEN),
        ("Koh Mui Huang", 75, Zone.WEST, ["Post-Op", "Mobility Support"], SeniorFeatures(75, 78, 94, 5.0, 800, 4, 0.55), "+65 9456 7890", RiskBand.RED),
        ("Lee Siu Ming", 82, Zone.CENTRAL, ["Dementia", "Companion"], SeniorFeatures(82, 65, 96, 4.5, 500, 2, 0.50), "+65 9567 8901", RiskBand.AMBER),
        ("Wong Kam Seng", 69, Zone.NORTH, ["Chronic Disease", "Mobility Support"], SeniorFeatures(69, 90, 93, 5.5, 1500, 3, 0.40), "+65 9678 9012", RiskBand.AMBER),
        ("Chen Yoke Lan", 85, Zone.SOUTH, ["Dementia"], SeniorFeatures(85, 70, 95, 4.0, 600, 5, 0.70), "+65 9789 0123", RiskBand.RED),
        ("Abdul Rahim", 73, Zone.EAST, ["Companion"], SeniorFeatures(73, 72, 98, 7.5, 4000, 0, 0.25), "+65 9890 1234", RiskBand.GREEN),
        ("Fatimah Binte Ahmad", 77, Zone.WEST, ["Mobility Support"], SeniorFeatures(77, 75, 94, 6.5, 2000, 2, 0.42), "+65 9901 2345", RiskBand.AMBER),
        ("Patel Ravi Kumar", 71, Zone.CENTRAL, ["Chronic Disease"], SeniorFeatures(71, 88, 92, 5.0, 1800, 3, 0.48), "+65 9012 3456", RiskBand.AMBER),
        ("Singh Harjeet", 79, Zone.NORTH, ["Post-Op"], SeniorFeatures(79, 68, 97, 6.0, 2200, 1, 0.35), "+65 9123 5678", RiskBand.GREEN),
        ("Norhaliza Binte Jamal", 74, Zone.SOUTH, ["Companion", "Mobility Support"], SeniorFeatures(74, 78, 96, 5.0, 1000, 2, 0.40), "+65 9234 6789", RiskBand.GREEN),
        ("Teo Ah Kiang", 81, Zone.EAST, ["Dementia", "Chronic Disease"], SeniorFeatures(81, 82, 93, 4.5, 700, 4, 0.60), "+65 9345 7890", RiskBand.RED),
        ("Goh Kwee Chuan", 67, Zone.WEST, ["Mobility Support"], SeniorFeatures(67, 70, 99, 7.0, 5000, 0, 0.20), "+65 9456 8901", RiskBand.GREEN),
        ("Boo Geok Hua", 76, Zone.CENTRAL, ["Companion"], SeniorFeatures(76, 74, 95, 6.0, 2800, 1, 0.35), "+65 9567 9012", RiskBand.GREEN),
        ("Lee Pei Ling", 83, Zone.NORTH, ["Dementia", "Post-Op"], SeniorFeatures(83, 78, 92, 4.0, 400, 6, 0.75), "+65 9678 0123", RiskBand.RED),
        ("Ang Bee Lian", 70, Zone.SOUTH, ["Chronic Disease"], SeniorFeatures(70, 85, 94, 5.5, 1600, 2, 0.38), "+65 9789 1234", RiskBand.GREEN),
        ("Nair Subramaniam", 75, Zone.EAST, ["Companion", "Chronic Disease"], SeniorFeatures(75, 80, 95, 6.5, 2100, 1, 0.32), "+65 9890 2345", RiskBand.GREEN),
        ("Raman Menon", 72, Zone.WEST, ["Mobility Support", "Companion"], SeniorFeatures(72, 72, 97, 6.0, 2400, 1, 0.30), "+65 9901 3456", RiskBand.GREEN),
        ("Mohammed Faizal", 68, Zone.CENTRAL, ["Chronic Disease", "Mobility Support"], SeniorFeatures(68, 88, 93, 5.0, 1300, 3, 0.45), "+65 9012 4567", RiskBand.AMBER),
    ]

    for i, (name, age, zone, care_needs, features, family_contact, risk_band) in enumerate(risk_data):
        seniors.append(Senior(
            id=f"S{i+1:02d}",
            name=name,
            age=age,
            zone=zone,
            care_needs=care_needs,
            care_hours=2.0,
            features=features,
            family_contact=family_contact,
            risk_band=risk_band
        ))

    return seniors

def generate_caregivers() -> List[Caregiver]:
    """Generate 5 caregivers."""
    return [
        Caregiver("CG01", "Nurse Aileen Tan", ["Nursing", "Dementia Care"], Zone.NORTH, [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]),
        Caregiver("CG02", "Nurse Bee Cheng", ["Nursing", "Chronic Disease"], Zone.SOUTH, [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]),
        Caregiver("CG03", "Care Diana", ["Dementia Care", "Companion"], Zone.EAST, [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]),
        Caregiver("CG04", "Care Erwin", ["Mobility Support", "Post-Op"], Zone.WEST, [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]),
        Caregiver("CG05", "Nurse Fatima", ["Nursing", "Companion"], Zone.CENTRAL, [Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI]),
    ]

def generate_accelerometer_sequence(sequence_type: str, n_samples: int = 150) -> np.ndarray:
    """Generate accelerometer data for a movement sequence.

    Args:
        sequence_type: "Normal Walk", "Shuffle Gait", or "Fall"
        n_samples: Number of samples (150 = 3 seconds at 50Hz)

    Returns:
        numpy array of shape (n_samples, 3) with X, Y, Z acceleration values
    """
    t = np.linspace(0, 3, n_samples)

    # Normalize sequence type for comparison
    seq_type_normalized = sequence_type.strip().lower().replace(" ", "_").replace("-", "_")

    if seq_type_normalized in ("normal_walk", "normal"):
        # Regular stride pattern with consistent vertical oscillation
        y = 1.0 + 0.2 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 0.05, n_samples)
        x = 0.1 * np.sin(2 * np.pi * 1 * t) + np.random.normal(0, 0.03, n_samples)
        z = 0.05 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.02, n_samples)

    elif seq_type_normalized in ("shuffle_gait", "shuffle"):
        # Short steps, reduced vertical range
        # Short steps, reduced vertical range
        y = 1.0 + 0.1 * np.sin(2 * np.pi * 1 * t) + np.random.normal(0, 0.08, n_samples)
        x = 0.15 * np.sin(2 * np.pi * 0.8 * t) + np.random.normal(0, 0.05, n_samples)
        z = 0.03 * np.random.normal(0, 1, n_samples)

    elif seq_type_normalized == "fall":
        # 5-phase: pre-fall (0-0.5s), free-fall (0.5-0.8s), rotation (0.8-1.0s), impact (1.0-1.2s), settle (1.2-3.0s)
        # 5-phase: pre-fall (0-0.5s), free-fall (0.5-0.8s), rotation (0.8-1.0s), impact (1.0-1.2s), settle (1.2-3.0s)
        y = np.zeros(n_samples)
        x = np.zeros(n_samples)
        z = np.zeros(n_samples)

        for i in range(n_samples):
            t_i = t[i]
            if t_i < 0.5:
                # Pre-fall: slight forward lean
                y[i] = 1.0 + 0.1 * np.sin(2 * np.pi * 2 * t_i)
                x[i] = 0.2 + 0.05 * np.random.normal()
            elif t_i < 0.8:
                # Free-fall: rapid vertical drop
                phase = (t_i - 0.5) / 0.3
                y[i] = 1.0 - 0.8 * phase + 0.05 * np.random.normal()
                x[i] = 0.3 + 0.3 * phase + 0.05 * np.random.normal()
            elif t_i < 1.0:
                # Rotation
                phase = (t_i - 0.8) / 0.2
                y[i] = 0.2 + 0.1 * np.sin(2 * np.pi * 4 * phase)
                x[i] = 0.6 + 0.4 * np.sin(2 * np.pi * 3 * phase) + 0.05 * np.random.normal()
                z[i] = 0.5 * np.sin(2 * np.pi * 2 * phase) + 0.05 * np.random.normal()
            elif t_i < 1.5:
                # Impact spike
                phase = (t_i - 1.0) / 0.5
                y[i] = 2.5 * np.exp(-3 * phase) + 0.3 * (1 - phase) + 0.05 * np.random.normal()
                x[i] = 0.8 * (1 - phase) + 0.05 * np.random.normal()
                z[i] = 0.3 * np.random.normal()
            else:
                # Settle to normal
                phase = (t_i - 1.5) / 1.5
                decay = np.exp(-2 * phase)
                y[i] = 1.0 + 0.3 * decay + 0.05 * np.random.normal()
                x[i] = 0.1 * decay + 0.05 * np.random.normal()
                z[i] = 0.02 * np.random.normal()
    else:
        # Default to normal walk if unknown type
        y = 1.0 + 0.2 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 0.05, n_samples)
        x = 0.1 * np.sin(2 * np.pi * 1 * t) + np.random.normal(0, 0.03, n_samples)
        z = 0.05 * np.sin(2 * np.pi * 0.5 * t) + np.random.normal(0, 0.02, n_samples)

    return np.column_stack([x, y, z])

def generate_preloaded_events() -> List[Event]:
    """Generate the 3 pre-loaded care events for L4."""
    now = datetime.now()
    return [
        Event(
            id="E1",
            senior_id="S01",
            senior_name="Tan Poh Lek",
            senior_age=78,
            event_type=EventType.FALL,
            timestamp=now,
            risk_band=RiskBand.RED,
            confidence=0.91,
            metadata={"zone": "North"}
        ),
        Event(
            id="E2",
            senior_id="S02",
            senior_name="Lim Sok Kuan",
            senior_age=72,
            event_type=EventType.SPO2_DROP,
            timestamp=now,
            risk_band=RiskBand.AMBER,
            confidence=0.0,
            metadata={"metric": "SpO2", "value": 91}
        ),
        Event(
            id="E3",
            senior_id="S03",
            senior_name="Ng Teck Seng",
            senior_age=80,
            event_type=EventType.MISSED_MEDS,
            timestamp=now,
            risk_band=RiskBand.GREEN,
            confidence=0.0,
            metadata={"doses_missed": 2}
        ),
    ]

# =============================================================================
# L1: FALL DETECTION
# =============================================================================

def extract_features(buffer: np.ndarray) -> np.ndarray:
    """Extract statistical features from accelerometer buffer.

    Args:
        buffer: numpy array of shape (150, 3) with X, Y, Z acceleration

    Returns:
        18-element feature vector (6 stats x 3 axes)
    """
    features = []
    for axis in range(3):
        axis_data = buffer[:, axis]
        features.append(np.mean(axis_data))
        features.append(np.std(axis_data))
        features.append(np.min(axis_data))
        features.append(np.max(axis_data))
        features.append(np.max(axis_data) - np.min(axis_data))  # range
        # Zero crossings (mean-centered)
        centered = axis_data - np.mean(axis_data)
        features.append(np.sum(np.diff(np.sign(centered)) != 0))
    return np.array(features)

class FallDetector:
    """Fall detection using sklearn RandomForest."""

    def __init__(self):
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self._train_model()

    def _train_model(self):
        """Train on synthetic labeled data."""
        X_train = []
        y_train = []

        for _ in range(50):
            seq = generate_accelerometer_sequence("Normal Walk")
            X_train.append(extract_features(seq))
            y_train.append(0)  # Normal

        for _ in range(30):
            seq = generate_accelerometer_sequence("Shuffle Gait")
            X_train.append(extract_features(seq))
            y_train.append(1)  # Shuffle

        for _ in range(30):
            seq = generate_accelerometer_sequence("Fall")
            X_train.append(extract_features(seq))
            y_train.append(2)  # Fall

        self.model.fit(X_train, y_train)

    def classify(self, buffer: np.ndarray) -> Dict[str, Any]:
        """Classify a movement sequence.

        Returns:
            dict with 'label', 'class_id', and 'confidence' for each class
        """
        features = extract_features(buffer).reshape(1, -1)
        probs = self.model.predict_proba(features)[0]
        class_id = np.argmax(probs)

        labels = ["Normal Walk", "Shuffle Gait", "Fall"]
        return {
            "label": labels[class_id],
            "class_id": class_id,
            "confidence": float(probs[class_id]),
            "all_probabilities": {
                labels[i]: float(p) for i, p in enumerate(probs)
            }
        }

# =============================================================================
# L2: HEALTH RISK DASHBOARD
# =============================================================================

class HealthRiskPredictor:
    """RandomForest-based health risk predictor with SHAP explainability."""

    def __init__(self, seniors: List[Senior]):
        from sklearn.ensemble import RandomForestClassifier
        import shap

        self.seniors = seniors
        self.feature_names = ["age", "resting_hr", "spo2", "sleep_hours", "step_count", "prev_hospitalisations", "frailty_index"]

        # Prepare training data
        X_train = []
        y_train = []
        for senior in seniors:
            f = senior.features
            X_train.append([f.age, f.resting_hr, f.spo2, f.sleep_hours, f.step_count, f.prev_hospitalisations, f.frailty_index])
            y_train.append(self._clinical_risk_label(senior))

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        self.model.fit(X_train, y_train)

        # Build SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)

    def _clinical_risk_label(self, senior: Senior) -> int:
        """Generate ground-truth risk label based on clinical rules."""
        f = senior.features
        if f.frailty_index > 0.6 or f.spo2 < 92 or f.prev_hospitalisations >= 4:
            return 2  # HIGH
        elif f.frailty_index > 0.4 or f.spo2 < 95 or f.prev_hospitalisations >= 2:
            return 1  # MEDIUM
        return 0  # LOW

    def predict(self, senior: Senior) -> RiskAssessment:
        """Predict risk for a senior."""
        f = senior.features
        features = [[f.age, f.resting_hr, f.spo2, f.sleep_hours, f.step_count, f.prev_hospitalisations, f.frailty_index]]
        probs = self.model.predict_proba(features)[0]
        pred_class = np.argmax(probs)

        labels = ["Low", "Medium", "High"]
        risk_level = RiskLevel[labels[pred_class].upper()]
        risk_score = probs[2] + 0.5 * probs[1]  # Composite score

        # SHAP values - convert to numpy array for shap
        features_np = np.array(features)
        raw_shap = self.explainer.shap_values(features_np)

        # Handle different array shapes from TreeExplainer
        # RandomForest returns shape (1, n_features, n_classes) - 3D
        if isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
            # Shape is (1, n_features, n_classes) - extract for predicted class
            shap_values = raw_shap[0, :, pred_class]
        elif isinstance(raw_shap, list):
            # Multi-class list: use the SHAP values for the predicted class
            shap_values = np.array(raw_shap[pred_class])
        elif len(raw_shap.shape) == 2:
            # 2D array: use the predicted class row
            shap_values = raw_shap[pred_class] if raw_shap.shape[0] > 1 else raw_shap[0]
        else:
            shap_values = np.array(raw_shap)

        factor_indices = np.argsort(np.abs(shap_values))[-3:][::-1]

        top_3_factors = []
        for idx in factor_indices:
            direction = "increases_risk" if shap_values[idx] > 0 else "decreases_risk"
            top_3_factors.append(SHAPFactor(
                feature_name=self.feature_names[idx],
                feature_value=features[0][idx],
                shap_value=float(shap_values[idx]),
                direction=direction
            ))

        return RiskAssessment(
            senior_id=senior.id,
            senior_name=senior.name,
            risk_level=risk_level,
            risk_score=float(risk_score),
            probabilities={labels[i]: float(p) for i, p in enumerate(probs)},
            top_3_factors=top_3_factors
        )

# =============================================================================
# L3: CARE SCHEDULE OPTIMISER
# =============================================================================

def solve_schedule(seniors: List[Senior], caregivers: List[Caregiver], cancelled_cg_id: str = None) -> Dict[str, Any]:
    """Solve caregiver schedule using OR-Tools MILP.

    Returns dict with schedule, solve_time_ms, and status.
    """
    from ortools.sat.python import cp_model

    active_caregivers = [cg for cg in caregivers if cg.id != cancelled_cg_id and cg.active]
    active_caregivers_dict = {cg.id: cg for cg in active_caregivers}

    model = cp_model.CpModel()

    # Decision variables: x[i,j] = 1 if caregiver i assigned to senior j
    x = {}
    for cg in active_caregivers:
        for senior in seniors:
            x[(cg.id, senior.id)] = model.NewBoolVar(f'x_{cg.id}_{senior.id}')

    # Helper variables for count per caregiver
    cg_senior_count = {}
    for cg in active_caregivers:
        cg_senior_count[cg.id] = sum(x[(cg.id, s.id)] for s in seniors)

    # Constraints
    # 1. Each senior assigned to at most one caregiver
    for senior in seniors:
        model.add(sum(x[(cg.id, senior.id)] for cg in active_caregivers) <= 1)

    # 2. Max 2 seniors per caregiver per day
    for cg in active_caregivers:
        model.add(cg_senior_count[cg.id] <= cg.max_seniors_per_day)

    # 3. Certification match
    for cg in active_caregivers:
        for senior in seniors:
            if not any(cert in cg.certifications for cert in senior.care_needs):
                model.add(x[(cg.id, senior.id)] == 0)

    # Objective: maximize same-zone assignments (soft constraint)
    zone_matches = []
    for cg in active_caregivers:
        for senior in seniors:
            var = x[(cg.id, senior.id)]
            is_same_zone = 1 if cg.home_zone == senior.zone else 0
            zone_matches.append(is_same_zone * var)

    model.Maximize(sum(zone_matches))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 4  # Parallel search
    solver.parameters.max_time_in_seconds = 5.0  # 5 second limit
    solver.parameters.stop_after_first_solution = True  # Stop at first feasible
    start_time = time.time()
    status = solver.solve(model)
    solve_time_ms = (time.time() - start_time) * 1000

    assignments = []
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for cg in active_caregivers:
            slots = []
            zone_match_count = 0
            for senior in seniors:
                if solver.value(x[(cg.id, senior.id)]):
                    zone_match = cg.home_zone == senior.zone
                    if zone_match:
                        zone_match_count += 1
                    slots.append(SeniorAssignment(
                        senior_id=senior.id,
                        senior_name=senior.name,
                        zone=senior.zone,
                        care_needs=senior.care_needs,
                        zone_match=zone_match
                    ))
            if slots:
                assignments.append(ScheduleAssignment(
                    caregiver_id=cg.id,
                    caregiver_name=cg.name,
                    day=Day.MON,
                    slots=slots,
                    zone_match_count=zone_match_count
                ))

    return {
        "schedule": assignments,
        "solve_time_ms": solve_time_ms,
        "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
        "unassigned": [s for s in seniors if not any(
            solver.value(x[(cg.id, s.id)]) for cg in active_caregivers
        )]
    }

# =============================================================================
# L4: CARE AGENT
# =============================================================================

def decide_actions(event: Event) -> List[str]:
    """Decision tree logic for care actions."""
    if event.event_type == EventType.FALL:
        if event.risk_band == RiskBand.RED:
            return ["EMS_DISPATCH", "FAMILY_ALERT", "NEHR_LOG"]
        elif event.risk_band == RiskBand.AMBER:
            return ["FAMILY_ALERT", "AMBULANCE_STANDBY", "NEHR_LOG"]
        else:
            return ["LOG_ONLY", "SCHEDULE_CHECK"]
    elif event.event_type == EventType.SPO2_DROP:
        if event.risk_band == RiskBand.RED:
            return ["EMS_DISPATCH", "FAMILY_ALERT", "NEHR_LOG", "POLYCLINIC_EMERGENCY"]
        elif event.risk_band == RiskBand.AMBER:
            return ["FAMILY_ALERT", "POLYCLINIC_BOOKING"]
        else:
            return ["LOG_ONLY", "SCHEDULE_CHECK"]
    elif event.event_type == EventType.MISSED_MEDS:
        if event.risk_band == RiskBand.GREEN:
            return ["SEND_REMINDER"]
        else:
            return ["LOG_ONLY", "SCHEDULE_CHECK"]
    return ["LOG_ONLY", "SCHEDULE_CHECK"]

def execute_action(action: str, event: Event) -> Dict[str, Any]:
    """Execute a care action and return log entry."""
    import json

    now = datetime.now()
    if action == "EMS_DISPATCH":
        return {
            "action": action,
            "message": f"Dispatching EMS to {event.metadata.get('zone', 'location')}",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "EMS_DISPATCH",
                "senior": event.senior_name,
                "zone": event.metadata.get("zone", "Unknown")
            })
        }
    elif action == "FAMILY_ALERT":
        return {
            "action": action,
            "message": f"Alerting family: +65 XXXX XXXX",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "FAMILY_ALERT",
                "senior": event.senior_name
            })
        }
    elif action == "NEHR_LOG":
        return {
            "action": action,
            "message": "Logging to NEHR...",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "NEHR_LOG",
                "senior": event.senior_name,
                "event_type": event.event_type.value
            })
        }
    elif action == "POLYCLINIC_BOOKING":
        return {
            "action": action,
            "message": "Booking polyclinic appointment",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "POLYCLINIC_BOOKING",
                "senior": event.senior_name
            })
        }
    elif action == "SEND_REMINDER":
        return {
            "action": action,
            "message": f"Sending medication reminder to {event.senior_name}",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "SEND_REMINDER",
                "senior": event.senior_name,
                "doses_missed": event.metadata.get("doses_missed", 0)
            })
        }
    elif action == "AMBULANCE_STANDBY":
        return {
            "action": action,
            "message": "Ambulance on standby",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "AMBULANCE_STANDBY",
                "senior": event.senior_name
            })
        }
    elif action == "LOG_ONLY":
        return {
            "action": action,
            "message": "Event logged for monitoring",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "LOG_ONLY",
                "senior": event.senior_name
            })
        }
    elif action == "SCHEDULE_CHECK":
        return {
            "action": action,
            "message": "Scheduling welfare check",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": "SCHEDULE_CHECK",
                "senior": event.senior_name
            })
        }
    else:
        return {
            "action": action,
            "message": f"Executing {action}",
            "timestamp": now.isoformat(),
            "json_log": json.dumps({
                "timestamp": now.isoformat(),
                "action": action,
                "senior": event.senior_name
            })
        }

# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def render_l1_page(fall_detector: FallDetector, sequences: Dict[str, np.ndarray]):
    """Render L1 Fall Detection page."""
    st.header("L1: Fall Detection")
    st.markdown("### Accelerometer Data Stream (3-axis, 50Hz)")

    # Sequence selector
    sequence_options = ["Normal Walk", "Shuffle Gait", "Fall"]
    selected = st.radio("Select Movement Sequence:", sequence_options, index=0)

    # Generate or retrieve sequence
    if selected not in sequences:
        sequences[selected] = generate_accelerometer_sequence(selected)

    buffer = sequences[selected]

    # Live chart
    chart_placeholder = st.empty()
    df = pd.DataFrame(buffer, columns=["X", "Y", "Z"])
    chart_placeholder.line_chart(df)

    # Classification
    result = fall_detector.classify(buffer)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Predicted Class", result["label"])
    with col2:
        st.metric("Confidence", f"{result['confidence']:.2%}")

    # Confidence gauge (simulated with bar)
    st.markdown("**Confidence by Class:**")
    conf_df = pd.DataFrame([
        {"Class": k, "Probability": v}
        for k, v in result["all_probabilities"].items()
    ])
    st.bar_chart(conf_df.set_index("Class"))

    # Alert
    if result["label"] == "Fall" and result["confidence"] >= 0.85:
        st.error("🚨 FALL DETECTED - Immediate Attention Required!")
        st.session_state.l1_alert_triggered = True
    else:
        st.session_state.l1_alert_triggered = False

    # Log
    st.markdown("### Classification Log")
    log_entry = {
        "Timestamp": datetime.now().strftime("%H:%M:%S"),
        "Class": result["label"],
        "Confidence": f"{result['confidence']:.2%}",
        "Alert": "YES" if st.session_state.l1_alert_triggered else "No"
    }
    st.session_state.l1_classification_log.append(log_entry)
    if st.session_state.l1_classification_log:
        log_df = pd.DataFrame(st.session_state.l1_classification_log[-10:])
        st.table(log_df)

def render_l2_page(risk_predictor: HealthRiskPredictor):
    """Render L2 Health Risk Dashboard page."""
    st.header("L2: Health Risk Dashboard")
    st.markdown("### 30-Day Readmission Risk Assessment")

    assessments = [risk_predictor.predict(s) for s in risk_predictor.seniors]
    assessments.sort(key=lambda a: a.risk_score, reverse=True)

    # Traffic light table
    st.markdown("**Tele-Nurse Worklist** (sorted by risk score)")
    rows = []
    for a in assessments:
        risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[a.risk_level.value]
        top_factors = ", ".join([f["feature_name"] for f in [
            {"feature_name": f.feature_name} for f in a.top_3_factors
        ]])
        rows.append({
            "Senior": a.senior_name,
            "Age": risk_predictor.seniors[[s.id for s in risk_predictor.seniors].index(a.senior_id)].age,
            "Risk Level": f"{risk_color} {a.risk_level.value}",
            "Risk Score": f"{a.risk_score:.2f}",
            "Top 3 Factors": top_factors
        })

    df = pd.DataFrame(rows)
    st.table(df)

    # SHAP detail for selected senior
    st.markdown("### SHAP Explanation Detail")
    senior_names = [a.senior_name for a in assessments]
    selected_senior = st.selectbox("Select Senior for SHAP Detail:", senior_names)
    selected_assessment = next(a for a in assessments if a.senior_name == selected_senior)

    st.markdown(f"**{selected_assessment.senior_name}** - Risk Level: {selected_assessment.risk_level.value}")
    st.markdown("**Top 3 Risk Factors:**")
    for factor in selected_assessment.top_3_factors:
        direction_icon = "↑" if factor.direction == "increases_risk" else "↓"
        st.write(f"- {direction_icon} {factor.feature_name}: {factor.feature_value:.3f} (SHAP: {factor.shap_value:.3f})")

    # Summary
    st.markdown("### Risk Distribution")
    risk_counts = pd.DataFrame([
        {"Risk Level": "High", "Count": sum(1 for a in assessments if a.risk_level == RiskLevel.HIGH)},
        {"Risk Level": "Medium", "Count": sum(1 for a in assessments if a.risk_level == RiskLevel.MEDIUM)},
        {"Risk Level": "Low", "Count": sum(1 for a in assessments if a.risk_level == RiskLevel.LOW)},
    ])
    st.bar_chart(risk_counts.set_index("Risk Level"))

def render_l3_page(seniors: List[Senior], caregivers: List[Caregiver]):
    """Render L3 Caregiver Schedule Optimiser page."""
    st.header("L3: Caregiver Schedule Optimiser")

    # Initial solve
    if not st.session_state.l3_schedule:
        result = solve_schedule(seniors, caregivers)
        st.session_state.l3_schedule = result["schedule"]
        st.session_state.l3_active_caregivers = [cg.id for cg in caregivers]
        st.session_state.l3_solve_time_ms = result["solve_time_ms"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Solve Time", f"{st.session_state.l3_solve_time_ms:.1f} ms")
    with col2:
        st.metric("Caregivers Active", len(st.session_state.l3_active_caregivers))

    # Cancel buttons
    st.markdown("### Caregiver Management")
    for cg in caregivers:
        if cg.id in st.session_state.l3_active_caregivers:
            if st.button(f"Cancel: {cg.name}", key=f"cancel_{cg.id}"):
                st.session_state.l3_active_caregivers.remove(cg.id)
                result = solve_schedule(seniors, caregivers, cancelled_cg_id=cg.id)
                st.session_state.l3_schedule = result["schedule"]
                st.session_state.l3_solve_time_ms = result["solve_time_ms"]
                st.rerun()
        else:
            st.button(f"Restored: {cg.name}", key=f"restore_{cg.id}", disabled=True)

    # Schedule display
    st.markdown("### Today's Schedule")
    for assignment in st.session_state.l3_schedule:
        with st.expander(f"{assignment.caregiver_name} ({assignment.zone_match_count} same-zone)"):
            for slot in assignment.slots:
                zone_color = "🟢" if slot.zone_match else "🟡"
                st.write(f"{zone_color} {slot.senior_name} - {', '.join(slot.care_needs)}")

    if not st.session_state.l3_schedule:
        st.warning("No feasible schedule found.")

def render_l4_page(events: List[Event], seniors: List[Senior], caregivers: List[Caregiver]):
    """Render L4 Care Agent page."""
    st.header("L4: Autonomous Care Agent")

    # Event triggers
    st.markdown("### Event Monitor")
    cols = st.columns(3)
    event_results = {}

    for i, event in enumerate(events):
        with cols[i]:
            if st.button(f"Trigger: {event.senior_name}", key=f"event_{event.id}"):
                actions = decide_actions(event)
                action_results = []
                for action in actions:
                    result = execute_action(action, event)
                    action_results.append(result)
                event_results[event.id] = {
                    "event": event,
                    "actions": actions,
                    "action_results": action_results,
                    "perception": f"{event.senior_name}, {event.senior_age}, {event.event_type.value}",
                    "reasoning": f"Rule match: {event.event_type.value} + {event.risk_band.value}"
                }
                st.session_state.l4_event_log.append({
                    "event": event,
                    "actions": actions,
                    "timestamp": datetime.now()
                })

    # Event details display
    st.markdown("### Perception → Reasoning → Action")
    for event_id, result in event_results.items():
        with st.expander(f"Event: {result['event'].senior_name}"):
            st.markdown(f"**PERCEPTION:** {result['perception']}")
            st.markdown(f"**REASONING:** {result['reasoning']}")
            st.markdown("**ACTIONS:**")
            for ar in result["action_results"]:
                st.write(f"- {ar['message']}")

    # Unified log placeholder
    st.markdown("### Event Log")
    if st.session_state.l4_event_log:
        log_df = pd.DataFrame([
            {
                "Time": e["timestamp"].strftime("%H:%M:%S"),
                "Senior": e["event"].senior_name,
                "Type": e["event"].event_type.value,
                "Actions": ", ".join(e["actions"])
            }
            for e in st.session_state.l4_event_log[-10:]
        ])
        st.table(log_df)

def render_typhoon_scenario(seniors: List[Senior], caregivers: List[Caregiver]):
    """Render Typhoon Scenario - integrated L3 + L4."""
    st.header("🌪️ Typhoon Scenario")
    st.warning("Demo Centrepiece: Mr Tan falls AND a caregiver cancels simultaneously")

    # Typhoon trigger button with debounce
    if st.session_state.l4_typhoon_countdown > 0:
        st.button(f"Typhoon Triggered! (Wait {st.session_state.l4_typhoon_countdown}s)", disabled=True)
    else:
        if st.button("🌪️ Trigger Typhoon Scenario"):
            # Sequential execution as per spec
            # T+0: Typhoon triggered
            # T+5: L3 receives cancellation, L4 perceives fall
            # T+10: L3 Solver starts

            # Find Tan Poh Lek (S01) and Nurse Aileen (CG01)
            tan = next(s for s in seniors if s.id == "S01")
            nurse_aileen = next(cg for cg in caregivers if cg.id == "CG01")

            # Create fall event for Tan
            event = Event(
                id="E1",
                senior_id=tan.id,
                senior_name=tan.name,
                senior_age=tan.age,
                event_type=EventType.FALL,
                timestamp=datetime.now(),
                risk_band=RiskBand.RED,
                confidence=0.91,
                metadata={"zone": tan.zone.value}
            )

            # L3: Solve with CG01 cancelled
            start = time.time()
            result = solve_schedule(seniors, caregivers, cancelled_cg_id="CG01")
            l3_time = (time.time() - start) * 1000

            # L4: Actions based on decision tree
            actions = decide_actions(event)
            action_results = [execute_action(a, event) for a in actions]

            # Add to unified log
            correlation_id = f"TYPHOON-{datetime.now().strftime('%H%M%S')}"
            st.session_state.l3_l4_unified_log.append(LogEntry(
                timestamp=datetime.now(),
                source="L3",
                event_type="SCHEDULE_REOPT",
                details={
                    "cancelled_caregiver": nurse_aileen.name,
                    "assignments": len(result["schedule"]),
                    "solve_time_ms": l3_time
                },
                correlation_id=correlation_id
            ))

            for ar in action_results:
                st.session_state.l3_l4_unified_log.append(LogEntry(
                    timestamp=datetime.now(),
                    source="L4",
                    event_type=ar["action"],
                    details={"message": ar["message"], "json": ar["json_log"]},
                    correlation_id=correlation_id
                ))

            # Set debounce
            st.session_state.l4_typhoon_countdown = 5
            st.rerun()

    # Display countdown
    if st.session_state.l4_typhoon_countdown > 0:
        st.info(f"Cooldown: {st.session_state.l4_typhoon_countdown}s remaining")

    # Unified log
    st.markdown("### Unified Event Log")
    if st.session_state.l3_l4_unified_log:
        for entry in st.session_state.l3_l4_unified_log[-20:]:
            color = "🔵" if entry.source == "L3" else "🟠"
            st.write(f"{color} [{entry.timestamp.strftime('%H:%M:%S')}] {entry.source}: {entry.event_type} - {entry.details}")
    else:
        st.info("Trigger typhoon to see unified log")

# =============================================================================
# MAIN APP
# =============================================================================

def render_welcome_page():
    """Render the welcoming home page with explanations."""
    st.title("🏥 AgeCareAI")
    st.markdown("### Smart Elder Care for Singapore")
    st.markdown("---")

    # Why this matters
    st.markdown("## 🤔 The Problem We're Solving")
    st.markdown("""
    Singapore has one of the fastest-aging populations in the world. By 2030, 1 in 4 Singaporeans
    will be over 65. Many elderly live alone or with family members who work full-time.

    **The challenge:** How do we make sure every elderly person gets the care they need,
    when they need it, without overwhelming caregivers and health systems?

    **Our answer:** An AI-powered system that works 24/7, helps caregivers prioritize,
    and responds to emergencies instantly.
    """)

    st.markdown("---")

    # Who benefits
    st.markdown("## 🎯 Who Benefits Most")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 👴👵 The Elderly")
        st.markdown("""
        **Direct benefit:** Faster response when accidents happen.

        - Falls detected immediately — no lying on the floor for hours
        - Health risks identified before they become emergencies
        - Medication reminders reduce missed doses
        - Same caregiver visits — building trust and familiarity
        """)
    with col2:
        st.markdown("### 👨‍👩‍👧 Families")
        st.markdown("""
        **Direct benefit:** Peace of mind, knowing AI is watching 24/7.

        - Instant alerts when something happens
        - Clear visibility into parent's health trends
        - Know that scheduling is optimized for their loved one
        - Less anxiety about parents living alone
        """)
    with col3:
        st.markdown("### 🏥 Healthcare System")
        st.markdown("""
        **Direct benefit:** Better resource allocation, reduced hospital readmissions.

        - Nurses see risk-ranked patient lists — focus energy where needed most
        - Schedule optimization reduces travel time, sees more patients per day
        - High-risk patients get preventive care, avoiding costly hospitalizations
        - Administrative burden reduced significantly
        """)

    st.markdown("---")

    # How the system works together
    st.markdown("## 🔗 How The 4 AI Layers Work Together")
    st.markdown("""
    AgeCareAI isn't 4 separate tools — it's **one integrated system** where each layer feeds into the next.
    Think of it like a well-coordinated care team:
    """)

    # Flow diagram as text
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                    THE AGE CARE AI SYSTEM                           │
    │                                                                     │
    │   LAYER 1                    LAYER 2                               │
    │   ┌─────────────┐           ┌─────────────┐                        │
    │   │ FALL         │           │ HEALTH      │                        │
    │   │ DETECTION    │──────────▶│ RISK        │                        │
    │   │ (Wearable    │  Falls   │ PREDICTION  │                        │
    │   │  Sensor)     │  trigger  │ (Dashboard) │                        │
    │   └─────────────┘           └─────────────┘                        │
    │         │                           │                               │
    │         │                           │ High-risk                    │
    │         │                           │ patients get                 │
    │         │                           │ priority                     │
    │         ▼                           ▼                               │
    │   ┌─────────────────────────────────────────────┐                   │
    │   │              LAYER 3                        │                   │
    │   │         CAREGIVER SCHEDULE                 │                   │
    │   │         OPTIMIZER                          │                   │
    │   │  • Same-zone preference                    │                   │
    │   │  • Skills matched to patient needs         │                   │
    │   │  • High-risk = higher visit priority       │                   │
    │   └─────────────────────────────────────────────┘                   │
    │                      │                                               │
    │                      │ When emergency happens:                      │
    │                      ▼                                               │
    │   ┌─────────────────────────────────────────────┐                   │
    │   │              LAYER 4                        │                   │
    │   │         CARE AGENT                          │                   │
    │   │  (Automatic Response System)                │                   │
    │   │  • Alert family immediately                │                   │
    │   │  • Call ambulance if fall + red risk       │                   │
    │   │  • Book polyclinic if vitals concerning   │                   │
    │   │  • Log everything to medical records       │                   │
    │   └─────────────────────────────────────────────┘                   │
    └─────────────────────────────────────────────────────────────────────┘
    ```
    """)

    st.markdown("---")

    # The workflow
    st.markdown("## ⚙️ How It Works In Practice")

    st.markdown("### Real-Time Monitoring vs. Daily Planning")
    st.markdown("""
    The system runs in **two modes simultaneously:**
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔴 24/7 Monitoring (L1 + L4)")
        st.markdown("""
        **Always watching** — even when no one is looking:

        - Wearable sensors on patients send data every second
        - L1 AI checks: "Is this a fall?"
        - If fall detected → L4 immediately alerts family + decides response
        - If vitals drop → L4 decides: family call? polyclinic? ambulance?

        **Result:** Average response time drops from hours to minutes.
        """)
    with col2:
        st.markdown("### 📅 Daily Planning (L2 + L3)")
        st.markdown("""
        **Every morning, the system prepares:**

        - L2 reviews all patients → ranks by readmission risk
        - L3 creates optimal schedule for each caregiver
        - High-risk patients get priority slots
        - If a caregiver calls in sick → L3 re-optimizes in milliseconds

        **Result:** Nurses spend less time planning, more time caring.
        """)

    st.markdown("---")

    # What each user does
    st.markdown("## 👤 What Each Person Does")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🧓 Elderly Patient")
        st.markdown("""
        **Their experience:**
        1. Wears a small sensor on their wrist (like a watch)
        2. Goes about their normal day
        3. If they fall, help comes automatically
        4. If they miss medication, they get a friendly reminder

        **They don't need to operate any app** — it's all automatic.
        """)
    with col2:
        st.markdown("### 👩‍⚕️ Nurse / Caregiver")
        st.markdown("""
        **Their experience:**
        1. Opens the dashboard each morning
        2. Sees their assigned patients, optimized by route and priority
        3. During visits, they see patient history and risk factors
        4. If urgent alert comes in, they know exactly what to do

        **They spend 80% less time on planning**, 80% more time on care.
        """)

    st.markdown("---")

    # Regional expansion
    st.markdown("## 🌍 Beyond Singapore")
    st.markdown("""
    Singapore is the first deployment because we understand the local context — the zones,
    healthcare system, and demographics. But **every developed nation faces the same challenge:**
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🇯🇵 Japan")
        st.markdown("""
        28% of population over 65.
        Most advanced aging society.
        Severe caregiver shortage.
        """)
    with col2:
        st.markdown("### 🇰🇷 South Korea")
        st.markdown("""
        Fastest aging population.
        Low birth rate amplifies problem.
        Already testing AI elder care.
        """)
    with col3:
        st.markdown("### 🇹🇼 Taiwan")
        st.markdown("""
        17% over 65, rising fast.
        Strong tech sector ready to help.
        Similar healthcare system to Singapore.
        """)

    st.markdown("""
    **After Singapore:** We can adapt the same AI system for any country.
    The core technology (fall detection, risk prediction, scheduling, care response)
    works anywhere. We just need to:
    1. Connect to local healthcare systems
    2. Train on local demographics
    3. Integrate with local emergency services
    """)

    st.markdown("---")

    # How to explore
    st.markdown("## 🔍 Explore the Demo")
    st.markdown("""
    Use the **left sidebar menu** to see each layer in action:

    | Page | What It Does | Who Benefits |
    |------|-------------|--------------|
    | **L1: Fall Detection** | Detects falls from wearable sensor data | Elderly, Families |
    | **L2: Health Risk** | Predicts 30-day readmission risk for each patient | Nurses, Healthcare System |
    | **L3: Schedule** | Optimizes caregiver assignments automatically | Caregivers, Patients |
    | **L4: Care Agent** | Automatically responds to emergencies | Everyone |

    **Start with L1** to see fall detection, then work your way up to L4!
    """)

def main():
    st.set_page_config(
        page_title="AgeCareAI - Elder Care Platform",
        page_icon="🏥",
        layout="wide"
    )

    init_session_state()

    # Sidebar navigation with "Home" option
    with st.sidebar:
        st.header("🏥 AgeCareAI")
        st.markdown("---")
        st.markdown("**Select a page:**")
        page_options = [
            "🏠 Home (Start Here)",
            "🦶 L1: Fall Detection",
            "📊 L2: Health Risk",
            "👩‍⚕️ L3: Caregiver Schedule",
            "🤖 L4: Care Agent"
        ]
        selected_page = st.radio(
            "Navigation:",
            page_options,
            index=0,
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.markdown("*AgeCareAI — Smart Elder Care for Singapore*")

    # Initialize data (only once)
    if 'seniors' not in st.session_state:
        st.session_state.seniors = generate_singapore_seniors()

    if 'caregivers' not in st.session_state:
        st.session_state.caregivers = generate_caregivers()

    if 'fall_detector' not in st.session_state:
        with st.spinner("Loading AI models..."):
            st.session_state.fall_detector = FallDetector()

    if 'risk_predictor' not in st.session_state:
        with st.spinner("Analyzing health risks..."):
            st.session_state.risk_predictor = HealthRiskPredictor(st.session_state.seniors)

    if 'sequences' not in st.session_state:
        st.session_state.sequences = {}

    if 'preloaded_events' not in st.session_state:
        st.session_state.preloaded_events = generate_preloaded_events()

    # Handle typhoon countdown
    if st.session_state.l4_typhoon_countdown > 0:
        st.session_state.l4_typhoon_countdown -= 1

    # Route to selected page
    if selected_page == "🏠 Home (Start Here)":
        render_welcome_page()
    elif selected_page == "🦶 L1: Fall Detection":
        render_l1_page(st.session_state.fall_detector, st.session_state.sequences)
    elif selected_page == "📊 L2: Health Risk":
        render_l2_page(st.session_state.risk_predictor)
    elif selected_page == "👩‍⚕️ L3: Caregiver Schedule":
        render_l3_page(st.session_state.seniors, st.session_state.caregivers)
    elif selected_page == "🤖 L4: Care Agent":
        render_typhoon_scenario(st.session_state.seniors, st.session_state.caregivers)
        st.divider()
        render_l4_page(st.session_state.preloaded_events, st.session_state.seniors, st.session_state.caregivers)

if __name__ == "__main__":
    main()
