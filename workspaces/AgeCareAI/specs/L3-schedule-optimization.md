# L3 — Caregiver Schedule Optimisation Specification

## Overview

OR-Tools MILP solver for optimal daily caregiver-to-senior assignment with real-time re-optimisation.

## Entity Specification

### Seniors (10)

| Senior      | Care Needs       | Zone    | Baseline Care Hours |
| ----------- | ---------------- | ------- | ------------------- |
| Mr Tan      | Dementia         | North   | 2                   |
| Mrs Lim     | Chronic Disease  | South   | 1.5                 |
| Mr Ng       | Mobility Support | East    | 2                   |
| Mdm Koh     | Post-Op Care     | West    | 2.5                 |
| Mr Lee      | Dementia         | Central | 2                   |
| Mrs Chen    | Companion        | North   | 1                   |
| Mr Abdul    | Chronic Disease  | South   | 1.5                 |
| Mdm Fatimah | Mobility Support | East    | 2                   |
| Mr Wong     | Post-Op Care     | West    | 2                   |
| Mrs Goh     | Companion        | Central | 1                   |

### Caregivers (5)

| Caregiver | Certifications           | Home Zone | Max Seniors/Day |
| --------- | ------------------------ | --------- | --------------- |
| Nurse A   | Nursing, Dementia        | North     | 2               |
| Nurse B   | Nursing, Chronic Disease | South     | 2               |
| Care C    | Dementia, Companion      | East      | 2               |
| Care D    | Mobility, Post-Op        | West      | 2               |
| Care E    | Nursing, Companion       | Central   | 2               |

## Constraint Specification

### Hard Constraints (Must Satisfy)

1. **Certification Match:** Caregiver must have certification for senior's care need
   - Dementia needs → Dementia certification
   - Chronic Disease → Nursing or Chronic Disease
   - Post-Op → Post-Op or Nursing
   - Mobility Support → Mobility certification
   - Companion → Companion certification

2. **Max 2 Seniors/Day:** No caregiver assigned to more than 2 seniors per day

3. **Availability:** Assignments only where caregiver is available

### Soft Constraints (Minimise Violations)

1. **Same-Zone Preference:** Prefer assignments where caregiver.home_zone == senior.zone
2. **Balanced Workload:** Minimise variance in total care hours per caregiver

## MILP Formulation

### Decision Variables

```
x[i,j] ∈ {0,1}  # Caregiver i assigned to Senior j
```

### Objective Function

```
Minimize: Σ(x[i,j] * zone_penalty[i,j]) + workload_variance_penalty
```

### Constraints

```
Σ(x[i,j] for j) ≤ 2                    ∀i (max 2 seniors per caregiver)
Σ(x[i,j] for i) = 1                    ∀j (each senior assigned exactly once)
x[i,j] ≤ certified[i,j]               ∀i,j (certification match)
x[i,j] ≤ available[i,j]               ∀i,j (availability)
```

## UI Components

### Schedule Display

- Table: Rows = Caregivers, Columns = Assigned Seniors
- Cell content: Senior name + care type + zone
- Colour coding: green (same zone), yellow (different zone)

### Caregiver Status

- Active caregivers shown with assignment count
- "Caregiver cancels" button per caregiver

### Performance Metrics

- Solve time (milliseconds)
- Objective value
- Constraint violations count

## Real-Time Re-optimisation

### "Caregiver Cancels" Button

1. Mark caregiver as unavailable
2. Re-run MILP solver
3. Display new optimal assignment
4. Highlight changes from previous assignment

### Performance Target

- Re-solve time < 500ms for full re-optimisation

## Data Generation

- Singapore zone mapping: North (Woodlands), South (CBD), East (Tampines), West (Jurong), Central (Newton)
- Travel time ignored (same-day assignments)
- Care hours per senior randomised within baseline ±0.5
