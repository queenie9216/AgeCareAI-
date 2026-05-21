# L4 — Autonomous Care Agent Specification

## Overview

Perception-Reasoning-Action AI agent monitoring simulated events and executing care protocols.

## Event Specification

### Pre-loaded Events

| Event ID | Senior      | Age | Event Type        | Confidence/Value | Risk Profile |
| -------- | ----------- | --- | ----------------- | ---------------- | ------------ |
| E1       | Tan Poh Lek | 78  | Fall Detected     | 0.91 confidence  | Red          |
| E2       | Mrs Lim     | 72  | SpO2 Drop         | 91%              | Amber        |
| E3       | Mr Ng       | 80  | Missed Medication | 2 doses          | Green        |

### Event Attributes

```python
Event {
    id: str
    senior_name: str
    age: int
    event_type: Fall | SPO2_DROP | MISSED_MEDS
    severity_value: float  # confidence or measurement
    risk_profile: Red | Amber | Green
    timestamp: datetime
    processed: bool
    actions_taken: List[str]
}
```

## Decision Tree Logic

### Rule Set

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

### Action Definitions

| Action               | Description                              | Priority        |
| -------------------- | ---------------------------------------- | --------------- |
| EMS_DISPATCH         | Call emergency ambulance                 | Immediate       |
| FAMILY_ALERT         | Notify next of kin                       | Immediate       |
| NEHR_LOG             | Log to National Electronic Health Record | Immediate       |
| POLYCLINIC_BOOKING   | Schedule polyclinic appointment          | Within 4 hours  |
| POLYCLINIC_EMERGENCY | Urgent polyclinic referral               | Within 1 hour   |
| AMBULANCE_STANDBY    | Place ambulance on standby               | Immediate       |
| SEND_REMINDER        | Send medication reminder message         | Low priority    |
| LOG_ONLY             | Log event for monitoring                 | Informational   |
| SCHEDULE_CHECK       | Schedule welfare check                   | Within 24 hours |

## Agent Loop

### Perception Phase

1. Monitor event feed (simulated)
2. Parse event attributes
3. Classify event severity
4. Update event status

### Reasoning Phase

1. Match event against decision tree
2. Identify applicable rules
3. Determine required actions
4. Check for conflicting actions

### Action Phase

1. Execute actions in priority order
2. Update action log
3. Update senior risk profile
4. Trigger L3 re-optimisation if needed (for caregiver-related events)

## UI Components

### Event Feed Display

- Real-time event log table
- Columns: Time, Senior, Event, Severity, Status, Actions
- Auto-scroll to latest

### Reasoning Visualization

- Step-by-step display:
  ```
  PERCEPTION: Mr Tan, 78, Fall Detected @ 0.91 confidence
  ↓
  REASONING: Rule match - FALL + RED → EMS_DISPATCH, FAMILY_ALERT, NEHR_LOG
  ↓
  ACTION: Dispatching EMS to Mr Tan's location
  ACTION: Alerting family: +65 9123 4567
  ACTION: Logging to NEHR...
  ```

### Typhoon Scenario

- Button: "Trigger Typhoon Scenario"
- When triggered:
  1. Mr Tan fall event fires (L4)
  2. Caregiver cancels (L3)
  3. Both L3 re-optimise AND L4 act within same second
  4. Unified event log shows both responses

## Unified Event Log

- Combined view of L3 scheduling events + L4 care actions
- Real-time updates
- Filterable by: All | L3 Only | L4 Only | Typhoon
- Timestamp + source layer + action details
