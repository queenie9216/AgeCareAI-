# DECISION: AgeCareAI Implementation Approach

## Decisions Made During /todos Phase

### Design Decisions (Approved)

| OD     | Decision             | Choice                  | Rationale                                                 |
| ------ | -------------------- | ----------------------- | --------------------------------------------------------- |
| OD-001 | L1 CNN Architecture  | sklearn RandomForest    | Simpler for demo, no PyTorch dependency complexity        |
| OD-002 | L2 SHAP Fallback     | Bar chart               | Users see meaningful output even on failure               |
| OD-003 | L4 Typhoon Debounce  | 5 second disable        | Prevents accidental double-trigger during demo            |
| OD-004 | L4 NEHR Log Format   | Structured JSON         | Better for healthcare audit compliance                    |
| OD-005 | L3 Schedule Priority | Certification over zone | Safety-critical: trained caregivers must match care needs |

## Implementation Approach

### Single-File Architecture

- All code in `app.py` for simplicity
- Modules defined within file (data_models, L1_detector, L2_risk, L3_scheduler, L4_agent)
- Streamlit radio button navigation between layers

### Milestone Ordering

1. Foundation (M1): Requirements, data models
2. Data (M2): Simulated data generation
3. Layer implementations (M3-M6): L1 → L2 → L3 → L4
4. Integration (M7): Typhoon scenario
5. Shell (M8): Navigation
6. Documentation (M9): decisions.md
7. Verification (M10): Testing

### Key Technical Choices

- RandomForest for L1 (sklearn) over PyTorch CNN
- CP-SAT solver from OR-Tools for L3 MILP
- SHAP TreeExplainer for L2 explainability
- Sequential-within-1000ms protocol for typhoon (L3 first, then L4)

## Timestamp

2026-05-21
