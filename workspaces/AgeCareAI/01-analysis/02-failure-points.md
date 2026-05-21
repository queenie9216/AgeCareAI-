# Failure Point Analysis — AgeCareAI

**Project:** Autonomous Elder Care Platform
**Analysis Date:** 2026-05-21
**Scope:** All 4 AI layers + integration layer + UI layer
**Complexity Assessment:** Moderate — 4 loosely-coupled ML/OR layers sharing a single Streamlit process

---

## Executive Summary

The AgeCareAI platform combines four distinct AI subsystems (CNN fall detection, XGBoost risk scoring, MILP scheduling, and a decision-tree care agent) in a single Streamlit application. The primary failure risks are: (1) the typhoon integration scenario where L3 and L4 must update simultaneously — the shared Streamlit session state is the critical shared resource; (2) L3's MILP solver returning infeasible results under real-time re-solve pressure; and (3) L1's confidence threshold creating false-negative risk for actual falls. The mitigation burden falls disproportionately on integration layer discipline — specifically explicit state ownership and atomic UI refreshes.

**Overall Risk Level:** Moderate

---

## Risk Register

| ID        | Layer       | Failure Point                                                  | Likelihood | Impact       | Severity     | Mitigation                                                                         |
| --------- | ----------- | -------------------------------------------------------------- | ---------- | ------------ | ------------ | ---------------------------------------------------------------------------------- |
| FP-L1-01  | L1          | CNN model weights fail to load                                 | Low        | High         | **High**     | Model file bundling + checksum verification at startup                             |
| FP-L1-02  | L1          | Sequence buffer overrun or underrun                            | Medium     | High         | **High**     | Ring buffer with overflow guard; minimum-fill check before inference               |
| FP-L1-03  | L1          | False negative: fall confidence below 0.85 threshold           | Medium     | Critical     | **Critical** | Secondary heuristic (peak acceleration magnitude) as fallback trigger              |
| FP-L1-04  | L1          | False positive: normal activity misclassified as fall          | Medium     | Medium       | **Medium**   | Temporal smoothing over confidence window; cooldowns between alerts                |
| FP-L2-01  | L2          | XGBoost model retrain corrupts in-memory state                 | Low        | High         | **High**     | Replace model atomically; never mutate shared object                               |
| FP-L2-02  | L2          | SHAP computation exceeds Streamlit render timeout              | Medium     | Medium       | **Medium**   | Cache SHAP values; async computation; fallback to top-3 feature list               |
| FP-L2-03  | L2          | Senior record missing required feature                         | Low        | High         | **High**     | Schema validation on data load; explicit default for missing fields                |
| FP-L2-04  | L2          | Risk score table sorts incorrectly on tie                      | Low        | Low          | **Low**      | Stable sort on risk_score desc + senior_id asc                                     |
| FP-L3-01  | L3          | MILP solver timeout on re-solve                                | Medium     | High         | **High**     | Timeout cap (default 5s); fallback to previous schedule if unmet                   |
| FP-L3-02  | L3          | Infeasible solution (constraints unsatisfiable)                | Medium     | High         | **High**     | Constraint relaxation loop; explicit infeasibility UI message                      |
| FP-L3-03  | L3          | Caregiver cancel removes only certified caregiver              | Medium     | High         | **High**     | Pre-check feasibility before accepting cancel; warn if schedule becomes infeasible |
| FP-L3-04  | L3          | Re-solve races with Streamlit rerun                            | Medium     | High         | **High**     | Lock mechanism around solver execution; disable button during solve                |
| FP-L4-01  | L4          | Decision tree fires wrong action branch                        | Low        | High         | **High**     | Truth table coverage test on all 3x3 event/risk combinations                       |
| FP-L4-02  | L4          | Event log ordering non-deterministic                           | Medium     | Medium       | **Medium**   | Append-only log with monotonically increasing sequence numbers                     |
| FP-L4-03  | L4          | Multiple events fire simultaneously causing conflict           | Low        | High         | **High**     | Event queue with sequential processing; conflict detection before action           |
| FP-INT-01 | Integration | Typhoon button triggers L3 + L4 simultaneously with state race | **High**   | **Critical** | **Critical** | Shared lock; L3 must complete before L4 reads its output                           |
| FP-INT-02 | Integration | Streamlit session state corrupted across layers                | Medium     | High         | **High**     | Typed session state wrapper; read/write validation                                 |
| FP-INT-03 | Integration | L3 re-solve invalidates L4's pending action                    | Medium     | High         | **High**     | L4 action commitment before L3 re-solve; abort-and-replan if schedule changes      |
| FP-UI-01  | UI          | Alert rendering delayed or dropped under load                  | Medium     | High         | **High**     | Dedicated alert queue; non-blocking render; audio/visual fallback                  |
| FP-UI-02  | UI          | Concurrent button clicks cause duplicate triggers              | **High**   | Medium       | **High**     | Debounce + disable-on-click pattern for all action buttons                         |
| FP-UI-03  | UI          | Streamlit rerun during MILP solve causes stale result display  | Medium     | Medium       | **Medium**   | Progress indicator; result versioning; explicit session state checkpoints          |

---

## Layer-by-Layer Failure Analysis

### L1 — Fall Detection (CNN)

#### FP-L1-01: CNN Model Loading Failure

**What could go wrong:** Model weights file is missing, corrupted, or mismatched version. On first inference call the CNN forward pass receives uninitialized tensors or wrong architecture, producing garbage confidence scores.

**Severity: High** — Silent wrong predictions (no fallback) could trigger unnecessary alerts or, more dangerously, miss actual falls.

**Mitigation:**

- Bundle model weights in the app package with SHA-256 checksum
- On app startup: load weights, run a single warm-up inference with known input, assert output shape and range
- If warm-up fails: surface error banner, do not proceed to live detection
- Log model version and checksum at startup for audit trail

#### FP-L1-02: Sequence Buffer Underrun or Overrun

**What could go wrong:** The 3-axis accelerometer ring buffer either (a) fills with fewer than the CNN's expected sequence length before an inference call, producing a shape mismatch; or (b) overruns, dropping the oldest samples and misaligning the temporal window. At 50Hz, 1 second of data = 50 samples; if the buffer requires 3 seconds and only 2.5 are available, inference runs on truncated data.

**Severity: High** — Underrun on an actual fall event would produce a confidence score on partial data, potentially below threshold.

**Mitigation:**

- Implement ring buffer with minimum-fill check: do not call CNN until buffer has `expected_sequence_length` samples
- Track buffer fill percentage; surface warning if running below 90% fill rate
- On overflow: log the drop and continue — partial drop of old samples is less harmful than inference failure

#### FP-L1-03: False Negative — Fall Missed

**What could go wrong:** A real fall occurs but the CNN outputs confidence < 0.85, so no alert fires. Root causes: unusual fall biomechanics not in training data, sensor placement variation, or clothing muffling accelerometer peaks.

**Severity: Critical** — Actual fall without alert is the worst-case failure in elder care.

**Mitigation:**

- Add a physics-based secondary trigger: peak resultant acceleration > 3g (free-fall + impact) within a 0.5s window, regardless of CNN confidence
- If secondary trigger fires but CNN confidence < 0.85: fire a "low-confidence fall alert" with amber classification and request human review
- Periodically log the distribution of missed-fall signals to retrain the CNN
- Set a hard cap: if any sensor axis peaks above 5g, fire alert regardless of CNN output

#### FP-L1-04: False Positive — Normal Activity Misclassified

**What could go wrong:** Normal walking, sitting down, or shuffling is misclassified as a fall with confidence >= 0.85, triggering a false EMS alert. This creates alarm fatigue for caregivers and responders.

**Severity: Medium** — Wasted EMS resources; potential fine or reputation impact.

**Mitigation:**

- Apply temporal smoothing: require confidence >= 0.85 for at least 2 consecutive inference windows before triggering alert
- Implement alert cooldown: after a fall alert, ignore all L1 alerts for 60 seconds (prevents alert storms during confused sensor data)
- Display confidence score prominently so caregivers can see borderline calls

---

### L2 — Health Risk Dashboard (XGBoost)

#### FP-L2-01: XGBoost Model Mutation During Inference

**What could go wrong:** If model retraining or hyperparameter updates happen in-place on a shared XGBoost object while another thread (Streamlit's rerun) reads the model, the inference results become undefined. XGBoost is not thread-safe for concurrent read-write.

**Severity: High** — Corrupted risk scores could misrank seniors, causing tele-nurses to deprioritize high-risk patients.

**Mitigation:**

- Load model once at startup; store as a frozen/final object
- If retraining is required mid-session: train new model object, validate, then atomically replace the session state's model reference
- Never mutate model state after initial load
- Log model replacement events with timestamp and triggering condition

#### FP-L2-02: SHAP Computation Timeout

**What could go wrong:** SHAP TreeExplainer on XGBoost with 20 seniors and 7 features is computationally cheap, but if the model grows or the explanation call is not cached, repeated SHAP computation blocks the Streamlit render thread, causing UI freeze.

**Severity: Medium** — UI freeze, not data corruption.

**Mitigation:**

- Compute SHAP values once on model load; cache in session state keyed by model checksum
- If SHAP for a specific senior is requested and not cached: compute in a background thread; show loading indicator
- Fallback: if SHAP computation exceeds 2s, display a ranked list of top-3 features by gain instead of SHAP values
- Log SHAP computation times to identify outliers

#### FP-L2-03: Missing Feature in Senior Record

**What could go wrong:** A senior's record is missing a required feature (e.g., `previous_hospitalisations` is null). XGBoost's `predict()` will likely error or return NaN, breaking the risk table render.

**Severity: High** — Table fails to render; no risk visibility for tele-nurses.

**Mitigation:**

- On data load: validate schema; fill missing numeric features with median of the cohort
- Fill missing categorical features with "Unknown"
- Surface a warning banner listing seniors with imputed values so nurses know which scores are estimated
- Validate record count matches expected (20 seniors); fail fast if mismatch

#### FP-L2-04: Risk Score Tie Sorting

**What could go wrong:** Two seniors have identical risk scores. Streamlit's default stable sort may reorder them between reruns, causing confusing jumps in the tele-nurse worklist.

**Severity: Low** — Cosmetic, but could cause confusion in a clinical workflow.

**Mitigation:**

- Sort by `risk_score DESC, senior_id ASC` — deterministic tiebreak
- Document sort order in UI footer

---

### L3 — Caregiver Schedule Optimizer (MILP)

#### FP-L3-01: MILP Solver Timeout on Re-solve

**What could go wrong:** When "Caregiver cancels" is clicked, the OR-Tools MILP solver is invoked with a deadline. Under complex constraint configurations (tight feasibility), the solver may time out before finding any solution, leaving the UI stuck showing "optimizing..." indefinitely.

**Severity: High** — Caregiver is left without a valid schedule; patients may miss care visits.

**Mitigation:**

- Set a hard timeout (default 5 seconds, configurable); return best solution found so far or declare infeasible
- Display solver progress: "Exploring solutions... (n solutions found)"
- If timeout fires without feasible solution: revert to previous valid schedule; surface a clear "Could not find optimal schedule — showing previous assignment" banner
- Log solver runtime and solution quality for capacity planning

#### FP-L3-02: Infeasible Constraint System

**What could go wrong:** After caregiver cancel + new senior additions, the constraint set becomes infeasible (e.g., a senior requires a certification no remaining caregiver holds). The solver returns empty-handed.

**Severity: High** — No valid schedule exists; care gaps persist.

**Mitigation:**

- Before invoking solver, run a feasibility pre-check: iterate over unscheduled seniors and verify at least one certified caregiver exists in their zone
- If pre-check fails: surface specific constraint conflict ("Mrs. Chen requires dementia-certified caregiver; none available in North zone")
- Implement constraint relaxation: iteratively drop soft constraints (same-zone preference) until a feasible solution is found
- Log relaxation steps so administrators can revise constraint definitions

#### FP-L3-03: Caregiver Cancel Leaves Senior Without Coverage

**What could go wrong:** The cancelled caregiver was the only one certified to handle a particular senior's needs. The re-solve correctly identifies infeasibility but the UI does not make this clear, and the senior is silently dropped from the schedule.

**Severity: High** — A vulnerable senior receives no care; no alert is raised.

**Mitigation:**

- Pre-flight before cancel: compute coverage impact; if any senior loses all coverage, block cancel and surface: "Cannot remove Caregiver X: Mrs. Chen (dementia, zone North) would have no certified caregiver"
- After any re-solve, verify all 10 seniors appear in output schedule; alert if any are missing
- Log coverage gaps with senior name and timestamp for compliance audit

#### FP-L3-04: Race Condition — Streamlit Rerun During Solve

**What could go wrong:** User clicks "Caregiver cancels" while Streamlit is already rerunning (e.g., from an L2 filter change). Two solver invocations race, producing undefined behavior: potentially two conflicting schedules, corrupted schedule state, or duplicate alerts.

**Severity: High** — Non-deterministic schedule state; possible data corruption.

**Mitigation:**

- Wrap solver invocation in an explicit session-state lock: set `l3_solver_running = True` on entry, `False` on exit
- Disable the "Caregiver cancels" button while `l3_solver_running == True`; show "Re-optimizing..." label
- Use Streamlit's `st.experimental_rerun` guard: if a rerun is triggered while `l3_solver_running`, defer the solver call to the next clean cycle
- All schedule reads go through a getter that raises if write-in-progress

---

### L4 — Autonomous Care Agent

#### FP-L4-01: Decision Tree Wrong Branch

**What could go wrong:** The decision tree logic has an error — given a fall event + red-risk senior, the wrong action fires (e.g., reminder only instead of EMS). This is a logic error in the branching condition, not a data issue.

**Severity: High** — Wrong clinical action; could result in delayed emergency response.

**Mitigation:**

- Write exhaustive truth table covering all 3 events x 3 risk levels (9 combinations); verify each maps to the correct action
- Unit test each branch independently with mock event data
- Add integration test: feed the full event sequence through the decision tree; assert log output matches expected actions
- Code review sign-off required on any decision tree condition change

#### FP-L4-02: Event Log Non-Deterministic Ordering

**What could go wrong:** The event log is appended to from multiple places (L1 alert, L3 re-solve, L4 decision), and the order in which simultaneous events appear varies between reruns. This makes audit trails confusing and potentially masks the sequence of a real incident.

**Severity: Medium** — Audit log inconsistency; not life-threatening but complicates incident review.

**Mitigation:**

- Assign each log entry a monotonically increasing integer ID (`sequence_number`) at write time — never reuse or reorder
- Log entries include: `sequence_number`, `timestamp_ms`, `source_layer`, `event_type`, `payload`
- Display log sorted by `sequence_number` ascending — deterministic regardless of render timing
- On session start, initialize sequence counter from last committed log entry; never reset

#### FP-L4-03: Simultaneous Event Conflict

**What could go wrong:** The typhoon scenario fires two events simultaneously: L1 detects Mr. Tan's fall AND L3 reports caregiver cancellation. The decision tree processes them in an undefined order, potentially handling the caregiver cancel before the fall alert, which could affect the fall response (e.g., if the cancelled caregiver was assigned to Mr. Tan).

**Severity: High** — Action ordering affects which caregiver is dispatched; wrong order could delay EMS.

**Mitigation:**

- Implement event queue: L1/L3 events are enqueued, not processed immediately
- Process events sequentially in queue order; each processed event is logged with its sequence number
- If two events arrive within the same 100ms window, process L1 events before L3 events (falls take priority)
- Conflict detection: before executing an action, check whether a conflicting pending event exists; if so, wait until queue drains before acting

---

### Integration Layer

#### FP-INT-01: Typhoon Scenario — L3/L4 State Race (CRITICAL)

**What could go wrong:** The typhoon button triggers L3 (MILP re-solve) and L4 (care agent decision) simultaneously. Without explicit synchronization, L4 may read L3's schedule mid-write — seeing a partial, invalid, or empty schedule — and make decisions on stale data. The output log would show a care decision based on a schedule that does not yet reflect the cancellation.

**Severity: Critical** — The demo centrepiece produces visibly wrong output; could be flagged as a critical bug in a Singapore MGMT 655 demo.

**Mitigation:**

- **Mandatory execution order:** Typhoon button handler must (1) acquire integration lock, (2) run L3 to completion, (3) read L3's final schedule, (4) run L4 with that schedule snapshot, (5) release integration lock
- Expose the lock in session state: `integration_lock = True` during combined operation; all L3/L4 reads check this flag and block if held
- Display combined output only after both complete; show a "Computing..." state during the lock hold
- Unit test: simulate typhoon trigger, assert L4 receives the post-re-solve schedule (not the pre-solve schedule)
- Add integration test: capture L3 schedule before and after; verify L4 action log references the post-solve schedule

#### FP-INT-02: Streamlit Session State Corruption

**What could go wrong:** Streamlit's `st.session_state` is a global dictionary shared across all layers. A bug in L2 data processing could accidentally overwrite L3's schedule object, or L4 could mutate a senior's risk score mid-read by L2. With no type enforcement, these corruptions are silent.

**Severity: High** — Silent wrong data; very difficult to debug.

**Mitigation:**

- Create typed wrapper classes for each layer's session state (`L1State`, `L2State`, `L3State`, `L4State`) with explicit `get()` and `set()` methods that validate input types
- On `set()`: raise `TypeError` if type mismatches expected; never coerce silently
- On startup: validate that session state keys are initialized; fail fast if missing
- Add `st.session_state._get_state().__dict__` snapshot logging at key boundaries for debugging
- Keep layer state keys namespaced: `l1_buffer`, `l2_model`, `l3_schedule`, `l4_event_log`

#### FP-INT-03: L3 Re-solve Invalidates L4's Pending Action

**What could go wrong:** L4 has decided to dispatch a specific caregiver to Mr. Tan based on the current schedule. Before that dispatch is logged, the caregiver cancels, triggering L3 re-solve. L4's logged action references a caregiver who is no longer assigned to Mr. Tan.

**Severity: High** — Care decision references a caregiver who will not show up; patient is stranded.

**Mitigation:**

- L4 commits an action only after reading a version-locked snapshot of L3's schedule
- L3 increments a `schedule_version` counter every time the schedule changes
- L4's action log entry includes the `schedule_version` it was based on
- After L3 re-solve: if L4's pending action references a caregiver removed in new schedule, surface a "Schedule changed — replanning" message and re-run L4
- Never allow L4 to fire an action based on stale schedule data; action commitment and schedule snapshot must be atomic

---

### UI Layer

#### FP-UI-01: Alert Rendering Delayed or Dropped

**What could go wrong:** L1 fires a fall alert, but the Streamlit render queue is backed up (e.g., a slow L2 SHAP computation is running). The alert's `st.error` or `st.warning` call is delayed 10+ seconds, or dropped entirely if the connection resets. In a real fall, delayed alerts reduce EMS response time.

**Severity: High** — Direct patient safety impact; delayed emergency response.

**Mitigation:**

- Use `st.empty()` placeholder for alerts; update the placeholder immediately on trigger without waiting for other renders
- Implement a client-side audio alert via `st.components.v1` embedding JavaScript that fires immediately when the alert state changes
- Keep alert state in a dedicated session state key (`l1_active_alert`); do not let other computations block its render
- Log alert fire timestamps server-side independent of UI render; if UI drops, the server-side log provides audit trail
- Add visual pulse animation to alert banner to draw attention

#### FP-UI-02: Concurrent Button Clicks — Duplicate Triggers

**What could go wrong:** A user double-clicks "Caregiver cancels" rapidly, or clicks it while a previous solve is still running. Two solver invocations are dispatched, corrupting the schedule state.

**Severity: High** — Same as FP-L3-04 but from UI rather than backend race.

**Mitigation:**

- All action buttons: disable immediately on first click using Streamlit's `disabled` parameter; re-enable only after the operation completes or fails
- Add 300ms debounce: capture first click timestamp; ignore subsequent clicks within 300ms window
- Display button state clearly: "Caregiver cancels" → "Cancelling..." (disabled) → "Done" or "Failed"
- On error: re-enable button only after displaying the error message so user can retry

#### FP-UI-03: Stale Result Display After Rerun

**What could go wrong:** Streamlit's automatic rerun after one widget change triggers a L3 re-solve while the user is viewing the results of a previous solve. The UI shows the old schedule briefly, then switches to new results mid-read, causing confusion.

**Severity: Medium** — User experience issue; could be mistaken as a data bug.

**Mitigation:**

- Display a `st.subheader` with schedule version and timestamp whenever results update
- Use `st.container` with key to ensure Streamlit replaces rather than patches the content
- Show "Last updated: HH:MM:SS" footer; if the timestamp hasn't changed, the display is stale and the rerun is pending
- Consider explicit "Refresh" button rather than relying on auto-rerun for critical data

---

## Cross-Cutting Concerns

### State Management Summary

The single biggest architectural risk is the shared `st.session_state` dictionary serving as the communication bus between all four layers. Without discipline:

- L2 could mutate a data structure L1 is reading
- L3 and L4 racing on the schedule object produces non-deterministic output
- The typhoon integration test will intermittently fail depending on Python's thread scheduler

**Recommended architecture:**

```
st.session_state
  l1: L1State (read-only from other layers)
  l2: L2State (read-only from other layers)
  l3: L3State (read by L4 only after L3 lock released)
  l4: L4State (append-only event log)
  _lock: IntegrationLock (controls L3→L4 sequencing)
  _version: dict[str, int] (version counters per layer)
```

### Testing Requirements

| Layer       | Unit Test                               | Integration Test                       | Regression Test                                    |
| ----------- | --------------------------------------- | -------------------------------------- | -------------------------------------------------- |
| L1          | CNN output shape, confidence bounds     | L1 buffer + CNN end-to-end             | Quick-start: simulate fall, verify alert fires     |
| L2          | Feature importance, risk score range    | L2 data load + XGBoost + SHAP          | Quick-start: 20 seniors render, risk table visible |
| L3          | Constraint satisfaction, solver timeout | L3 cancel + re-solve + schedule output | Quick-start: cancel caregiver, schedule updates    |
| L4          | Truth table (9 combinations)            | L4 event + decision log                | Quick-start: fire 3 events, verify log order       |
| Integration | Lock correctness (concurrent access)    | Typhoon: L3+L4 simultaneous            | Quick-start: click typhoon, both outputs visible   |
| UI          | Button debounce, alert render           | Streamlit rerun during solve           | Quick-start: full app navigable                    |

---

## Recommended Verification Protocol

Before any implementation begins:

1. **FP-INT-01 must be verified with a deterministic integration test** — not a manual click-through. The test must assert that L4 receives the post-re-solve schedule, not the pre-solve schedule, under typhoon trigger. If this test cannot be written before implementation, implement a temporary synchronous execution path.

2. **FP-L1-03 (false negative) and FP-L1-04 (false positive) require a labeled test dataset.** At minimum: 10 normal walk sequences, 5 shuffle gait sequences, 5 fall sequences. Each sequence should be labeled ground truth. The CNN should score >= 0.90 recall and <= 0.10 false positive rate on this dataset before production deployment.

3. **FP-L3-02 (infeasibility) and FP-L3-03 (coverage gap) must be tested with edge-case constraint configurations** — specifically when the constraint system is at the boundary of feasibility. Use synthetic scenarios: 1 caregiver remaining, 10 seniors all requiring unique certifications.

---

## Success Criteria

- [ ] L1: Fall alert fires within 2s of simulated fall; false positive rate < 10% on test dataset
- [ ] L2: Risk table renders all 20 seniors; SHAP values load within 3s
- [ ] L3: Re-solve completes within 5s or returns previous valid schedule with banner
- [ ] L4: All 9 event/risk combinations produce correct actions per truth table
- [ ] Integration: Typhoon button produces L3 schedule AND L4 action log referencing the same post-re-solve schedule
- [ ] UI: All action buttons debounced; no duplicate triggers in 10-click stress test
- [ ] All layer state isolated by namespace; no cross-layer mutation observable
