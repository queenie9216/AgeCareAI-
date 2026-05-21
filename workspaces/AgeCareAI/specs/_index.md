# AgeCareAI Specification Index

## Domain Specs

| Spec File                     | Domain                   | Description                                                                   |
| ----------------------------- | ------------------------ | ----------------------------------------------------------------------------- |
| `L1-fall-detection.md`        | L1 Fall Detection        | CNN classifier for accelerometer data, 3-axis 50Hz stream, 3 activity classes |
| `L2-health-risk.md`           | L2 Health Risk Dashboard | XGBoost risk classifier, SHAP explainability, 20-senior dataset               |
| `L3-schedule-optimization.md` | L3 Caregiver Scheduler   | OR-Tools MILP, 10 seniors / 5 caregivers, constraint satisfaction             |
| `L4-care-agent.md`            | L4 Autonomous Care Agent | Perception-Reasoning-Action loop, decision tree, event processing             |
| `integration.md`              | Integration              | Typhoon scenario, cross-layer state, real-time updates                        |
| `data-models.md`              | Data Layer               | Senior, Caregiver, Event, Risk data structures                                |

## Traceability

Each brief requirement maps to at least one spec file. Missing mappings are blocking.
