# L2 — Health Risk Dashboard Specification

## Overview

XGBoost-powered 30-day readmission risk prediction with SHAP explainability for tele-nurse worklist prioritization.

## Dataset Specification

### Senior Records (20 seniors)

| Feature               | Type  | Range     | Description                      |
| --------------------- | ----- | --------- | -------------------------------- |
| age                   | int   | 65-90     | Age in years                     |
| resting_hr            | int   | 55-100    | Resting heart rate (bpm)         |
| spo2                  | int   | 88-100    | Blood oxygen saturation (%)      |
| sleep_hours           | float | 3.5-9.0   | Average nightly sleep            |
| step_count            | int   | 500-10000 | Daily average steps              |
| prev_hospitalisations | int   | 0-8       | Hospital admissions in past year |
| frailty_index         | float | 0.0-1.0   | Clinical frailty scale score     |

### Risk Labels

- **Low Risk:** 30-day readmission probability < 0.25
- **Medium Risk:** 30-day readmission probability 0.25-0.60
- **High Risk:** 30-day readmission probability > 0.60

## Model Specification

### XGBoost Classifier

```python
xgb.XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective='multi:softprob',
    num_class=3,
    eval_metric='mlogloss'
)
```

### Training

- Train/test split: 80/20
- Stratified sampling to maintain class distribution
- Feature importance from XGBoost built-in importance

## SHAP Integration

### Per-Senior Explanation

- Compute SHAP values for each senior record
- Display top 3 contributing factors
- Visualization: beeswarm plot for global, force plot for individual

### Risk Factor Interpretation

| Factor                | High-Risk Direction            |
| --------------------- | ------------------------------ |
| age                   | Higher → increased risk        |
| resting_hr            | Higher (>80) → increased risk  |
| spo2                  | Lower (<94) → increased risk   |
| sleep_hours           | Lower (<6) → increased risk    |
| step_count            | Lower (<2000) → increased risk |
| prev_hospitalisations | Higher → increased risk        |
| frailty_index         | Higher (>0.5) → increased risk |

## UI Components

### Dashboard Layout

1. **Risk Table**
   - Columns: Senior Name, Age, Risk Level, Risk Score, Top 3 Factors
   - Sorted by risk score (highest first)
   - Color-coded rows: 🔴 High | 🟡 Medium | 🟢 Low

2. **SHAP Detail Panel**
   - Select senior from table
   - Show force plot of SHAP values
   - Top 3 factors with directional arrows

3. **Summary Statistics**
   - Risk distribution pie chart
   - Average risk score
   - High-risk count

## Tele-Nurse Worklist

- Primary view: seniors sorted by risk score
- Quick actions (display only): Call, Send Reminder, Schedule Visit
- Filter by risk level

## Data Generation

Realistic Singapore demographic:

- Names: Singaporean Chinese/Malay/Indian names
- Ages: skewed toward 70-85
- Comorbidities reflected in feature correlations
