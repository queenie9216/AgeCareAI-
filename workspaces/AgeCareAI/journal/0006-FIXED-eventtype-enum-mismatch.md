# FIXED: EventType Enum Mismatch Between Spec and Code

## Issue

The EventType enum in app.py used `VITALS` and `MEDICATION` but the spec (data-models.md and L4-care-agent.md) defined `SPO2_DROP` and `MISSED_MEDS`. This caused a mismatch where:

- Spec: `Fall | SPO2_DROP | MISSED_MEDS`
- Code: `FALL | VITALS | MEDICATION`

The decision tree in `decide_actions()` used `EventType.VITALS` and `EventType.MEDICATION`, but the pre-loaded events also used these inconsistent values.

## Fix Applied

Updated app.py EventType enum (line 39-43):

```python
# Before
class EventType(Enum):
    FALL = "Fall Detected"
    VITALS = "Vitals Drop"
    MEDICATION = "Missed Medication"

# After
class EventType(Enum):
    FALL = "Fall Detected"
    SPO2_DROP = "SpO2 Drop"
    MISSED_MEDS = "Missed Medication"
```

Updated all references in:

- `generate_preloaded_events()` - E2 uses `EventType.SPO2_DROP`, E3 uses `EventType.MISSED_MEDS`
- `decide_actions()` - decision tree now uses `EventType.SPO2_DROP` and `EventType.MISSED_MEDS`

Updated L4-care-agent.md spec to use `SPO2_DROP | MISSED_MEDS` in Event attributes section.

## Verification

AST analysis confirms:

- EventType enum has values: FALL, SPO2_DROP, MISSED_MEDS
- decide_actions() uses: EventType.FALL, EventType.SPO2_DROP, EventType.MISSED_MEDS
- generate_preloaded_events() uses: EventType.FALL, EventType.SPO2_DROP, EventType.MISSED_MEDS

## Note

XGBoost requires libomp on Mac (`brew install libomp`). This is an environment dependency, not a code issue. The app compiles successfully and core modules (L1, L3, L4) work correctly.

## Timestamp

2026-05-21
