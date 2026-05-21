# GAP: 5 Open Design Decisions Requiring User Input

## Finding

Requirements breakdown identified 5 design decisions that need user approval before implementation.

## Decision List

### 1. L1 CNN Architecture Choice

- Option A: PyTorch 1D CNN (more accurate, requires torch dependency)
- Option B: sklearn RandomForest with statistical features (simpler, no torch)
- **Recommended:** Option B for simplicity unless accurate fall detection is critical

### 2. L2 SHAP Fallback UX

- Option A: Show simplified bar chart if SHAP computation fails
- Option B: Hide SHAP panel if computation fails
- **Recommended:** Option A with error message

### 3. L4 Typhoon Debounce

- Option A: Disable typhoon button for 5 seconds after trigger
- Option B: Allow immediate re-trigger
- **Recommended:** Option A to prevent spam

### 4. L4 NEHR Log Format

- Option A: Plain text log entry
- Option B: Structured JSON entry
- **Recommended:** Option B for consistency

### 5. L3 Schedule Conflict Priority

- Option A: Prioritise same-zone assignments over certification match
- Option B: Prioritise certification match over zone
- **Recommended:** Option B (certification is safety-critical)

## Status

Awaiting user input before /implement can proceed
