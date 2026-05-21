# Data Models Specification

## Senior Model

```python
@dataclass
class Senior:
    id: str
    name: str
    age: int
    care_needs: List[CareType]  # Dementia, ChronicDisease, PostOp, Mobility, Companion
    zone: Zone  # North, South, East, West, Central
    care_hours: float
    risk_profile: RiskLevel  # Red, Amber, Green

    # L2 features
    resting_hr: int
    spo2: int
    sleep_hours: float
    step_count: int
    prev_hospitalisations: int
    frailty_index: float
```

## Caregiver Model

```python
@dataclass
class Caregiver:
    id: str
    name: str
    certifications: List[Certification]  # Nursing, Dementia, etc.
    home_zone: Zone
    available: bool
    max_seniors_per_day: int = 2

    # Runtime
    assigned_seniors: List[str] = field(default_factory=list)
```

## Zone Enum

```python
class Zone(Enum):
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    CENTRAL = "Central"
```

## Care Type Enum

```python
class CareType(Enum):
    DEMENTIA = "Dementia"
    CHRONIC_DISEASE = "Chronic Disease"
    POST_OP = "Post-Op"
    MOBILITY = "Mobility Support"
    COMPANION = "Companion"
```

## Certification Enum

```python
class Certification(Enum):
    NURSING = "Nursing"
    DEMENTIA = "Dementia"
    CHRONIC_DISEASE = "Chronic Disease"
    POST_OP = "Post-Op"
    MOBILITY = "Mobility"
    COMPANION = "Companion"
```

## Risk Level Enum

```python
class RiskLevel(Enum):
    RED = "Red"      # High risk
    AMBER = "Amber"  # Medium risk
    GREEN = "Green"  # Low risk
```

## Event Model

```python
@dataclass
class Event:
    id: str
    senior: Senior
    event_type: EventType  # FALL, SPO2_DROP, MISSED_MEDS
    severity_value: float  # confidence or measurement
    timestamp: datetime
    processed: bool = False
    actions_taken: List[str] = field(default_factory=list)

class EventType(Enum):
    FALL = "Fall Detected"
    SPO2_DROP = "SpO2 Drop"
    MISSED_MEDS = "Missed Medication"
```

## Schedule Model

```python
@dataclass
class Schedule:
    date: date
    assignments: Dict[Caregiver, List[Senior]]  # who cares for whom
    unassigned_seniors: List[Senior]
    solve_time_ms: float
    objective_value: float
    status: ScheduleStatus

class ScheduleStatus(Enum):
    OPTIMAL = "Optimal"
    FEASIBLE = "Feasible"
    INFEASIBLE = "Infeasible"
    TIMEOUT = "Timeout"
```

## Action Model

```python
@dataclass
class Action:
    name: str
    description: str
    priority: Priority
    target: str  # senior_id or caregiver_id
    status: ActionStatus
    timestamp: datetime

class Priority(Enum):
    IMMEDIATE = 1
    URGENT = 2
    STANDARD = 3
    LOW = 4
```

## Simulated Data Generation

### Singapore Senior Names

Chinese: Tan, Lee, Ng, Wong, Chen, Goh, Lim, Koh, Teo, Ang
Malay: Abdul, Fatimah, Rahim, Aminah, Ibrahim, Zainab
Indian: Nair, Patel, Singh, Raman, Kumari

### Zone Mapping

North: Woodlands, Sembawang, Yishun
South: CBD, Outram, Tiong Bahru
East: Tampines, Bedok, Pasir Ris
West: Jurong, Clementi, Bukit Batok
Central: Newton, Toa Payoh, Bishan
