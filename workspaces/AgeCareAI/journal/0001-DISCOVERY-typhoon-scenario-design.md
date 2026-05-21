# DISCOVERY: Typhoon Scenario Cross-Layer Coupling

## Finding

The typhoon scenario requires tight cross-layer coordination between L3 (scheduler) and L4 (care agent). L4's EMS dispatch must respect L3's new caregiver schedule after re-optimisation.

## Details

- Typhoon = Mr Tan fall (L4) + Nurse A cancellation (L3)
- L3 re-optimises in <500ms
- L4 actions (EMS, family alert, NEHR log) execute simultaneously
- L4's event log entries include L3 schedule update references

## Implication

The unified event log must maintain correlation IDs across layers so actions reference the correct schedule state.

## Status

Logged for implementation planning
