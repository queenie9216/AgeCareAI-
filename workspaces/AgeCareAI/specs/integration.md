# Integration Specification

## Overview

Cross-layer integration demonstrating real-time coordination, with typhoon scenario as demo centrepiece.

## Layer Dependencies

```
L4 (Care Agent)
    ↓ triggers
L3 (Scheduler) ←→ L2 (Risk) ←→ L1 (Fall Detection)
```

## State Sharing

### Session State Structure

```python
st.session_state = {
    # L1 State
    'l1_current_sequence': str,
    'l1_classification_log': List[dict],
    'l1_alert_triggered': bool,

    # L2 State
    'l2_seniors_df': DataFrame,
    'l2_risk_predictions': Dict[str, float],
    'l2_shaps': Dict[str, np.array],

    # L3 State
    'l3_schedule': Dict[Caregiver, List[Senior]],
    'l3_active_caregivers': List[str],
    'l3_solve_time_ms': float,

    # L4 State
    'l4_event_log': List[Event],
    'l4_actions_taken': Dict[str, List[str]],
    'l4_typhoon_active': bool,

    # Cross-layer
    'l3_l4_unified_log': List[LogEntry],
}
```

## Typhoon Scenario Specification

### Trigger Condition

Single button click triggers simultaneous:

1. **L4 Event:** Mr Tan fall detected (0.91 confidence, red-risk)
2. **L3 Event:** One caregiver (Nurse A) marked as cancelled

### Coordination Protocol (CORRECTED)

The typhoon scenario uses a sequential-within-1000ms pattern: L3 must complete before L4 reads the final schedule.

```
T+0ms:   Typhoon triggered
T+5ms:   L3 receives cancellation event, L4 perceives Mr Tan fall
T+10ms:  L3 Solver starts re-optimisation (L4 waits)
T+50ms:  L3 Solver returns new schedule
T+55ms:  L4 reads final L3 schedule (CORRECT: L4 acts on post-reopt state)
T+60ms:  L4 Reasoning: Fall+Red → EMS + Family + NEHR
T+65ms:  L4 Actions execute against post-reopt schedule
T+100ms: Both outputs displayed in unified log
```

**Critical:** L4 actions (EMS dispatch, family alert) must reference the post-re-optimization schedule, not the pre-cancellation schedule. This is enforced by the sequential execution order.

### Unified Event Log Entry

```python
{
    'timestamp': '10:23:45.100',
    'source': 'L3',  # or 'L4'
    'event': 'SCHEDULE_UPDATE' | 'CARE_ACTION',
    'details': {...},
    'correlation_id': 'TYPHOON-001'
}
```

## Real-Time Update Mechanism

### Streamlit Callbacks

- Button click triggers state update
- `st.rerun()` forces UI refresh
- Timer-based polling for background tasks

### Threading Considerations

- OR-Tools solver runs in main thread (blocking)
- Event processing is synchronous
- Future enhancement: async processing

## Demo Flow

### Standard Demo Sequence

1. Navigate L1: Show fall detection with 3 sequences
2. Navigate L2: Show risk dashboard with SHAP
3. Navigate L3: Show optimized schedule, click "Caregiver cancels"
4. Navigate L4: Show event processing, trigger typhoon

### Typhoon Demo

1. Click "Trigger Typhoon Scenario"
2. Watch unified log: L3 schedule updates + L4 actions appear together
3. Verify timing: Both complete within 1 second
4. Show that L4's EMS dispatch still respects new L3 schedule

## Performance Targets

| Operation            | Target             |
| -------------------- | ------------------ |
| L1 classification    | < 50ms per window  |
| L2 SHAP computation  | < 200ms per senior |
| L3 initial solve     | < 500ms            |
| L3 re-solve (cancel) | < 500ms            |
| L4 event processing  | < 100ms            |
| Typhoon combined     | < 1000ms total     |
