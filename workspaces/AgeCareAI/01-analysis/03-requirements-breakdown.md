# AgeCareAI — Requirements Breakdown

## Document Identity

- **Project:** AgeCareAI — Autonomous Elder Care Platform
- **Phase:** 01-analysis
- **Source:** `briefs/001-initial-brief.md`
- **Tech stack:** Python, Streamlit, XGBoost+SHAP (L2), OR-Tools/MILP (L3), scikit-learn+PyTorch (L1), numpy/pandas/plotly

---

## 1. Functional Requirements Per Layer

### L1 — Fall Detection (CNN)

| REQ    | Description                             | Input                             | Output                             | Business Logic                                                                | Edge Cases                                         |
| ------ | --------------------------------------- | --------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------- |
| L1-001 | Simulate 3-axis accelerometer stream    | None (internal simulation)        | 3-element float array per timestep | Generates at 50Hz; cycles through 3 pre-loaded sequences                      | Sequence loop must wrap cleanly                    |
| L1-002 | Pre-load movement sequences             | None (on init)                    | Internal state: 3 named sequences  | Sequences: normal_walk, shuffle_gait, fall_event; each is a fixed numpy array | If sequence fails to load, raise RuntimeError      |
| L1-003 | CNN classifier inference                | Single timestep window (N frames) | Dict: {label, confidence}          | Lightweight CNN (PyTorch); confidence in [0.0, 1.0]                           | Model weights missing → raise FileNotFoundError    |
| L1-004 | Visual alert on fall confidence >= 0.85 | L1-003 output                     | Streamlit UI: red banner           | Alert disappears when confidence drops below 0.85                             | Alert must not persist if classifier flips rapidly |
| L1-005 | Live classification log                 | L1-003 output                     | Streamlit UI: scrolling log widget | Log shows timestamp + label + confidence per inference cycle                  | Log capped at 100 entries to prevent memory growth |
| L1-006 | Real-time loop control                  | 50Hz tick                         | Inference triggered                | Uses Streamlit `st.empty` placeholder; re-renders at native refresh           | Must not block Streamlit event loop                |

### L2 — Health Risk Dashboard (XGBoost)

| REQ    | Description                                   | Input                          | Output                                                | Business Logic                                                                                       | Edge Cases                                                             |
| ------ | --------------------------------------------- | ------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| L2-001 | Load 20-senior dataset                        | CSV or dict in-memory          | List[Senior]                                          | Dataset fields: age, resting_hr, spo2, sleep_hours, step_count, prev_hospitalisations, frailty_index | Missing any field → raise ValueError                                   |
| L2-002 | XGBoost 3-class risk classifier               | Senior feature vector (7 dims) | {risk_level: low/medium/high, raw_score: float}       | 3-class (low/medium/high); probabilities for all 3 classes stored                                    | Model not trained → raise RuntimeError before UI renders               |
| L2-003 | Traffic-light risk table                      | L2-002 output per senior       | Streamlit table: Senior Name, Risk, Score, Top Factor | Red=#d62728, Amber=#ff7f0e, Green=#2ca02c; sorted by risk_score desc                                 | All seniors same-risk → table still renders, sorting is stable         |
| L2-004 | SHAP values for top-3 risk factors per senior | L2-002 output + explainer      | Streamlit display: 3 factor names + bar chart         | One SHAP explainer pre-built on model init; per-senior TreeExplainer outputs                         | SHAP explainer build failure → fall back to feature importance display |
| L2-005 | Sorted display by risk score                  | All L2-002 outputs             | Table sorted high→low                                 | Risk score = P(high) + 0.5\*P(medium) as composite sort key                                          | Ties broken by senior name alphabetically                              |

### L3 — Caregiver Schedule Optimiser (MILP)

| REQ    | Description                                          | Input                              | Output                                                     | Business Logic                                                                     | Edge Cases                                                  |
| ------ | ---------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| L3-001 | Define 10 senior instances                           | In-memory data                     | Senior dataclass instances                                 | Fields: id, name, care_needs (list[str]), zone (N/S/E/W/Central)                   | Zone not in enum → raise ValueError                         |
| L3-002 | Define 5 caregiver instances                         | In-memory data                     | Caregiver dataclass instances                              | Fields: id, name, certifications (list[str]), zone, availability (list[day])       | Cert list empty → caregiver can only do companionship       |
| L3-003 | MILP schedule solver                                 | L3-001 + L3-002 + hard constraints | Dict: {caregiver_id: [(senior_id, slot)]}                  | OR-Tools CP-SAT; objective: maximise same-zone assignments; hard constraints below | Infeasible problem → display "No feasible schedule" message |
| L3-004 | Hard constraint: certification match                 | L3-003                             | Boolean feasibility                                        | Every assigned senior.care_needs must be subset of caregiver.certifications        | Unassignable seniors displayed separately                   |
| L3-005 | Hard constraint: max 2 seniors per caregiver per day | L3-003                             | Boolean feasibility                                        | Sum assignments per caregiver per day <= 2                                         | Solver must respect; not soft constraint                    |
| L3-006 | Soft constraint: same-zone preference                | L3-003                             | Objective minimisation term                                | Penalise cross-zone assignments by zone_mismatch_cost in objective                 | Does not make infeasible; only reduces score                |
| L3-007 | "Caregiver cancels" button                           | Streamlit button click             | Re-run L3-003 with one caregiver removed from availability | Re-optimise in <500ms; display updated schedule                                    | Button disabled during re-solve                             |
| L3-008 | Schedule display per caregiver                       | L3-003 output                      | Streamlit expanders: each caregiver's daily assignments    | Colour-coded by zone; cancelled caregivers shown greyed                            | Empty schedule shows "No assignments"                       |

### L4 — Autonomous Care Agent

| REQ    | Description                                              | Input                  | Output                               | Business Logic                                                                                                  | Edge Cases                                            |
| ------ | -------------------------------------------------------- | ---------------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| L4-001 | Event feed monitoring                                    | Event stream           | Streamlit UI: event cards            | Monitors 3 pre-loaded events; cycles through on timer or manual trigger                                         | Events must not duplicate in feed                     |
| L4-002 | Pre-loaded events: Mr Tan fall                           | None                   | Event dict                           | Event: {senior: "Mr Tan", age: 78, type: "fall", confidence: 0.91, risk_band: "red"}                            | Confidence is static pre-set value                    |
| L4-003 | Pre-loaded events: Mrs Lim SpO2 drop                     | None                   | Event dict                           | Event: {senior: "Mrs Lim", age: 72, type: "vitals", metric: "SpO2", value: 91, risk_band: "amber"}              | Value is static pre-set value                         |
| L4-004 | Pre-loaded events: Mr Ng missed meds                     | None                   | Event dict                           | Event: {senior: "Mr Ng", age: 80, type: "medication", doses_missed: 2, risk_band: "green"}                      | Doses_missed is static pre-set value                  |
| L4-005 | Decision rule: fall + red = EMS + family + NEHR          | Event L4-002           | Action log + UI updates              | Actions: (1) Dispatch EMS to zone, (2) Alert family (sms/notification), (3) Log to NEHR                         | Each action timestamped in reasoning log              |
| L4-006 | Decision rule: vitals drop + amber = family + polyclinic | Event L4-003           | Action log + UI updates              | Actions: (1) Alert family, (2) Book polyclinic appointment                                                      | Polyclinic booking shows as "pending confirmation"    |
| L4-007 | Decision rule: missed meds + green = reminder only       | Event L4-004           | Action log + UI updates              | Action: Send reminder notification to senior                                                                    | No escalation                                         |
| L4-008 | Perception → Reasoning → Action visual                   | L4-005/006/007 output  | Streamlit expandable: 3-step display | Step 1 (Perception): raw event data; Step 2 (Reasoning): rule matched + factors; Step 3 (Action): taken actions | All 3 steps always shown for traceability             |
| L4-009 | "Trigger typhoon scenario" button                        | Streamlit button click | Simultaneous L3 + L4 update          | (1) Mr Tan fall event fires, (2) One caregiver in Mr Tan's zone cancels simultaneously                          | L3 re-optimises + L4 acts within same 2-second window |
| L4-010 | Unified event log for typhoon                            | L4-009                 | Streamlit scrollable log             | Shows L3 schedule changes AND L4 actions interleaved chronologically                                            | Different colour per layer (L3=blue, L4=orange)       |

---

## 2. Data Models

### Senior

```python
@dataclass
class Senior:
    id: str                       # Unique, e.g. "S01"
    name: str                     # e.g. "Mr Tan"
    age: int                      # 65-100
    zone: Zone                   # Enum: N, S, E, W, Central
    care_needs: list[str]         # e.g. ["medication", "physio", "companionship"]
    features: SeniorFeatures     # For L2

@dataclass
class SeniorFeatures:
    age: int
    resting_hr: int              # 40-120 bpm
    spo2: int                    # 70-100 %
    sleep_hours: float           # 0.0-12.0
    step_count: int              # 0-20000
    prev_hospitalisations: int   # 0-20
    frailty_index: float         # 0.0-1.0
```

### Caregiver

```python
@dataclass
class Caregiver:
    id: str                       # Unique, e.g. "C01"
    name: str                     # e.g. "Nurse Aileen"
    certifications: list[str]     # e.g. ["medication", "physio", "dementia_care"]
    zone: Zone                   # Enum: N, S, E, W, Central
    availability: list[Day]       # e.g. [MON, TUE, WED, THU, FRI]

class Zone(Enum):
    N = "North"
    S = "South"
    E = "East"
    W = "West"
    Central = "Central"

class Day(Enum):
    MON = "Monday"
    TUE = "Tuesday"
    WED = "Wednesday"
    THU = "Thursday"
    FRI = "Friday"
```

### Event

```python
@dataclass
class Event:
    id: str                       # Unique event id
    senior_id: str                 # Links to Senior.id
    senior_name: str
    senior_age: int
    event_type: EventType          # Enum: fall, vitals, medication
    timestamp: datetime
    risk_band: RiskBand            # Enum: red, amber, green
    metadata: dict                 # Type-specific fields

class EventType(Enum):
    FALL = "fall"
    VITALS = "vitals"
    MEDICATION = "medication"

class RiskBand(Enum):
    RED = "red"     # High risk
    AMBER = "amber" # Medium risk
    GREEN = "green" # Low risk

# Fall event metadata keys: {confidence: float}
# Vitals event metadata keys: {metric: str, value: float}
# Medication event metadata keys: {doses_missed: int}
```

### Risk Assessment (L2 Output)

```python
@dataclass
class RiskAssessment:
    senior_id: str
    senior_name: str
    risk_level: RiskLevel          # Enum: LOW, MEDIUM, HIGH
    risk_score: float              # Composite sort key in [0.0, 1.0]
    probabilities: dict            # {LOW: float, MEDIUM: float, HIGH: float}
    top_3_factors: list[SHAPFactor]

@dataclass
class SHAPFactor:
    feature_name: str
    feature_value: float
    shap_value: float
    direction: str                 # "increases_risk" or "decreases_risk"
```

### Schedule Assignment (L3 Output)

```python
@dataclass
class ScheduleAssignment:
    caregiver_id: str
    day: Day
    slots: list[SeniorAssignment]

@dataclass
class SeniorAssignment:
    senior_id: str
    senior_name: str
    zone: Zone
    care_needs: list[str]
    zone_match: bool               # True if caregiver.zone == senior.zone
```

---

## 3. API / State Interfaces Between Layers

### Layer Communication Map

```
briefs/001-initial-brief.md
         │
         ▼
┌─────────┐    event stream    ┌─────────┐    schedule     ┌─────────┐
│   L1    │ ──────────────────►│   L4    │◄───────────────►│   L3    │
│  Fall   │   no direct link   │ Agent   │   re-optimise   │ Schedule│
│ Detect  │                   │         │                 │ Optimiser│
└─────────┘                   └─────────┘                 └─────────┘
                                    │
                                    │ risk lookup
                                    ▼
                              ┌─────────┐
                              │   L2    │
                              │  Risk   │
                              │Dashboard │
                              └─────────┘
```

### L1 → L4 Interface

- **Trigger channel:** When L1 detects fall with confidence >= 0.85, it emits an `Event` object with `event_type=FALL`
- **Payload:** `{senior_id: str, senior_name: str, event_type: FALL, confidence: float, timestamp: datetime}`
- **Transport:** In-process function call; no serialization
- **Contract:** L1 does not await L4 response; L4 processes asynchronously

### L4 → L3 Interface (Typhoon)

- **Trigger channel:** Typhoon button fires both L4 event + L3 cancel simultaneously
- **L4 payload to L3:** `{type: "caregiver_cancel", caregiver_id: str, day: Day}`
- **L3 response to L4:** Updated `ScheduleAssignment` dict
- **Transport:** In-process; shared `ScheduleState` object
- **Contract:** L3 must respond within 500ms for typhoon scenario to feel simultaneous

### L4 → L2 Interface

- **Query:** L4 event contains `senior_id`; L4 queries L2 for `RiskAssessment` by senior_id
- **Response:** `RiskAssessment` object with risk_band confirmation
- **Transport:** In-process function call against in-memory L2 state
- **Contract:** L2 always has the senior — dataset is pre-loaded

### L3 → UI State

- **State object:** `ScheduleState` (shared Streamlit session state via `st.session_state`)
- **Fields:** `{assignments: dict, last_updated: datetime, is_solving: bool, cancel_events: list}`
- **Update protocol:** L3 writes directly to `st.session_state["schedule_state"]`; UI reads on next tick

### L2 → UI State

- **State object:** `RiskDashboardState`
- **Fields:** `{assessments: list[RiskAssessment], last_updated: datetime, sort_key: str}`
- **Update protocol:** Recomputes on L2 data change only; cached otherwise

### Cross-Layer Event Bus (L4 Internal)

```python
class EventBus:
    def publish(self, event: Event) -> None: ...
    def subscribe(self, handler: Callable[[Event], None]) -> None: ...

# L4 modules subscribe to EventBus; L1/L3 publish to it
# Enables loose coupling between L4 perception/reasoning/action modules
```

---

## 4. Acceptance Criteria Per Layer

### L1 — Fall Detection

| AC     | Criterion                                                                      | Verification Method                       |
| ------ | ------------------------------------------------------------------------------ | ----------------------------------------- |
| L1-AC1 | App starts with 3 pre-loaded accelerometer sequences loaded in <2s             | `time.time()` around sequence loading     |
| L1-AC2 | CNN model loads and returns inference within 100ms per window                  | Timer around `model(input_tensor)`        |
| L1-AC3 | Visual red alert appears within 1 inference cycle when fall confidence >= 0.85 | UI inspection; confirm banner renders     |
| L1-AC4 | Alert disappears when fall sequence ends and confidence drops                  | Confirm banner hides                      |
| L1-AC5 | Classification log shows timestamp, label, confidence for each cycle           | Log entry count matches expected          |
| L1-AC6 | Streamlit UI remains responsive (no blocking loop)                             | UI interactions testable during inference |

### L2 — Health Risk Dashboard

| AC     | Criterion                                                        | Verification Method                             |
| ------ | ---------------------------------------------------------------- | ----------------------------------------------- |
| L2-AC1 | All 20 seniors display in table                                  | Row count == 20                                 |
| L2-AC2 | Risk classification matches XGBoost model output                 | Sample 3 seniors, verify vs manual calculation  |
| L2-AC3 | Traffic-light colours match risk bands exactly (red/amber/green) | CSS colour inspection                           |
| L2-AC4 | Table sorted by risk_score descending                            | Assert row[i].risk_score >= row[i+1].risk_score |
| L2-AC5 | SHAP top-3 factors display for each senior                       | 3 bars per senior in SHAP plot                  |
| L2-AC6 | SHAP explainer builds without error on app init                  | No exception in logs                            |

### L3 — Caregiver Schedule Optimiser

| AC     | Criterion                                                        | Verification Method                                                       |
| ------ | ---------------------------------------------------------------- | ------------------------------------------------------------------------- |
| L3-AC1 | All 10 seniors appear in schedule assignments or unassigned list | Covered seniors count <= 10                                               |
| L3-AC2 | No caregiver assigned >2 seniors on same day                     | Iterate all assignments; assert max_per_day <= 2                          |
| L3-AC3 | Every assignment has valid certification match                   | For each assignment, assert care_needs subset of caregiver.certifications |
| L3-AC4 | Initial solve completes in <1s                                   | Timer around OR-Tools solve                                               |
| L3-AC5 | "Caregiver cancels" re-solve completes in <500ms                 | Timer around re-solve                                                     |
| L3-AC6 | Cancelled caregiver shown greyed in display                      | CSS class applied correctly                                               |

### L4 — Autonomous Care Agent

| AC     | Criterion                                                           | Verification Method                            |
| ------ | ------------------------------------------------------------------- | ---------------------------------------------- |
| L4-AC1 | Mr Tan fall event triggers all 3 actions (EMS, family, NEHR)        | Count actions in log == 3                      |
| L4-AC2 | Mrs Lim SpO2 event triggers exactly 2 actions (family, polyclinic)  | Count actions == 2                             |
| L4-AC3 | Mr Ng missed meds triggers exactly 1 action (reminder)              | Count actions == 1                             |
| L4-AC4 | Perception-Reasoning-Action steps visible for each event            | 3 expanders visible per event                  |
| L4-AC5 | Typhoon button triggers L3 re-optimise AND L4 action simultaneously | Two types of log entries within 2s window      |
| L4-AC6 | Unified log shows L3 and L4 entries interleaved chronologically     | Sorted by timestamp; alternating layer colours |

---

## 5. Edge Cases

### L1 Edge Cases

| ID     | Scenario                                                                  | Expected Behaviour                                                          |
| ------ | ------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| E1-001 | Model weights file corrupted                                              | Raise FileNotFoundError; app shows error banner; L2/L3/L4 remain functional |
| E1-002 | Accelerometer sequence file missing                                       | Raise RuntimeError on L1 init; L2/L3/L4 unaffected                          |
| E1-003 | Confidence exactly 0.85 (boundary)                                        | Alert fires (>= 0.85 inclusive)                                             |
| E1-004 | Rapid oscillation between fall and normal (confidence flipping 0.84/0.86) | Alert shows/hides each cycle; no debounce required per brief                |
| E1-005 | Sequence loops back to start                                              | Seamless transition; no gap in accelerometer data                           |
| E1-006 | Fall detected during Streamlit rerun                                      | Inference result queued; no dropped detection                               |

### L2 Edge Cases

| ID     | Scenario                                                 | Expected Behaviour                                                |
| ------ | -------------------------------------------------------- | ----------------------------------------------------------------- |
| E2-001 | All 20 seniors classified as HIGH risk                   | Table all red; scrollable; still sorted                           |
| E2-002 | All 20 seniors classified as LOW risk                    | Table all green; scrollable; still sorted                         |
| E2-003 | SHAP explainer fails for one senior (rare feature combo) | Graceful fallback to feature importance; no crash                 |
| E2-004 | Senior feature values out of training range              | Model extrapolates; SHAP may be unreliable; display warning note  |
| E2-005 | Two seniors with identical risk scores                   | Tie broken by name alphabetically; deterministic                  |
| E2-006 | SpO2 value exactly 90% (amber/red boundary)              | If threshold is <90=amber, >=90=red; verify model threshold       |
| E2-007 | XGBoost model not yet trained on first run               | Pre-train at app init; show spinner; block L2 display until ready |

### L3 Edge Cases

| ID     | Scenario                                                  | Expected Behaviour                                            |
| ------ | --------------------------------------------------------- | ------------------------------------------------------------- |
| E3-001 | Infeasible schedule (constraints unsatisfiable)           | Display "No feasible schedule found" message; no crash        |
| E3-002 | All caregivers cancel (all unavailable)                   | Infeasible; same as E3-001                                    |
| E3-003 | Senior with care needs no caregiver can satisfy           | Senior listed in "Unassigned" section; no runtime error       |
| E3-004 | Re-solve triggered while previous solve in progress       | Cancel in-progress solve; start new one; no race condition    |
| E3-005 | Caregiver cancels at boundary (last available for a zone) | Some senior may become unassignable; shown in unassigned list |
| E3-006 | Two caregivers cancel simultaneously                      | Re-solve with 2 fewer caregivers; may result in infeasible    |
| E3-007 | Zone mismatch penalty calculation overflow                | OR-Tools handles internally; no user-visible error            |

### L4 Edge Cases

| ID     | Scenario                                                 | Expected Behaviour                                                            |
| ------ | -------------------------------------------------------- | ----------------------------------------------------------------------------- |
| E4-001 | Event arrives while previous event still reasoning       | Queue events; process sequentially; no dropped events                         |
| E4-002 | Typhoon button pressed rapidly multiple times            | Debounce 5s; second press ignored during cooldown                             |
| E4-003 | Mr Tan fall event arrives but caregiver not in same zone | L3 still re-optimises for zone; L4 EMS dispatch uses senior's zone            |
| E4-004 | Family contact info missing for a senior                 | Log warning; EMS dispatch still fires; family alert skipped                   |
| E4-005 | NEHR system simulated (no real log)                      | All NEHR actions logged to in-app log only; no external call                  |
| E4-006 | Polyclinic booking on weekend                            | Booking shown as "pending next weekday"; no error                             |
| E4-007 | Green-risk event escalates unexpectedly                  | All decision rules are static; no dynamic escalation                          |
| E4-008 | L3 solve takes >2s during typhoon                        | L4 action still fires; schedule update delayed; user sees spinner on L3 panel |

### Integration Edge Cases

| ID     | Scenario                                      | Expected Behaviour                                                  |
| ------ | --------------------------------------------- | ------------------------------------------------------------------- |
| E5-001 | Streamlit navigation between layers mid-event | Events not lost; state persists in `st.session_state`               |
| E5-002 | User switches tab during typhoon scenario     | Typhoon completes in background; user can return to see results     |
| E5-003 | App runs on reduced memory device (2GB RAM)   | All datasets in-memory; no memory-mapped files; no crash            |
| E5-004 | Rapid navigation: L1→L4→L3→L2 in <5s          | All layers initialise lazily; no blocking on navigation             |
| E5-005 | Browser tab inactive (hidden)                 | Streamlit continues running server-side; no special handling needed |

---

## 6. Non-Functional Requirements

| NFR     | Requirement                    | Target                                                         |
| ------- | ------------------------------ | -------------------------------------------------------------- |
| NFR-001 | Startup time                   | All 4 layers initialised and navigable within 10s on first run |
| NFR-002 | L1 inference latency           | Single window inference < 100ms                                |
| NFR-003 | L3 initial solve               | < 1000ms                                                       |
| NFR-004 | L3 re-solve (cancel)           | < 500ms                                                        |
| NFR-005 | Memory footprint               | < 500MB total (Python + model weights + dataset)               |
| NFR-006 | Single `streamlit run` command | No additional services, no database, no external API calls     |
| NFR-007 | Typhoon L3+L4 simultaneity     | Both complete within 2000ms window                             |

---

## 7. Cross-Reference Audit

| Check                                                    | Finding                                              |
| -------------------------------------------------------- | ---------------------------------------------------- |
| Brief L4-002 vs Requirements L4-002                      | Match: Mr Tan, 78, fall 0.91, red-risk               |
| Brief L4-003 vs Requirements L4-003                      | Match: Mrs Lim, 72, SpO2 91%, amber                  |
| Brief L4-004 vs Requirements L4-004                      | Match: Mr Ng, 80, missed 2 meds, green               |
| Brief L3 hard constraints vs Requirements L3-004/005/006 | Match: cert match, max 2/day, same-zone preference   |
| Brief Typhoon vs Requirements L4-009                     | Match: Mr Tan fall + caregiver cancel simultaneously |
| Brief L2 20 seniors vs Data Model Senior count           | Consistent: 20 seniors in dataset                    |
| Brief L3 10 seniors/5 caregivers vs Data Model           | Consistent: 10 seniors, 5 caregivers                 |

---

## 8. Open Design Decisions (Require User Input)

| OD     | Decision Point                        | Options                                                                            | Risk If Deferred                     |
| ------ | ------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------ |
| OD-001 | Fall detection model architecture     | Option A: PyTorch CNN (full control) vs Option B: scikit-learn MLP (simpler)       | Different accuracy/latency trade-off |
| OD-002 | SHAP explainer fallback               | Option A: Feature importance bar chart vs Option B: Show "explanation unavailable" | User experience difference           |
| OD-003 | Typhoon button debounce period        | Option A: 5s vs Option B: No debounce                                              | Rapid re-fire risk vs usability      |
| OD-004 | NEHR log format                       | Option A: Structured JSON log vs Option B: Plain text log                          | Compliance/readability               |
| OD-005 | Schedule conflict resolution priority | Option A: Prefer high-risk seniors vs Option B: Alphabetical                       | Different care distribution outcomes |
