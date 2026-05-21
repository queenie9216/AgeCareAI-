# AgeCareAI — Autonomous Elder Care Platform

Singapore

## Four AI Layers

| Layer  | Function              | Technology                             |
| ------ | --------------------- | -------------------------------------- |
| **L1** | Fall Detection        | RandomForest on accelerometer data     |
| **L2** | Health Risk Dashboard | RandomForest + SHAP explainability     |
| **L3** | Caregiver Scheduler   | OR-Tools MILP optimization             |
| **L4** | Care Agent            | Decision tree with typhoon integration |

## Deployment

### Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `app.py` as the main file
5. Deploy

**Requirements:** Python 3.9+, all dependencies in `requirements.txt`

## Project Structure

```
AgeCareAI/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── specs/                 # Detailed specifications
├── 01-analysis/          # Analysis documents
├── 02-plans/              # Implementation plans
├── 03-user-flows/        # User flow documentation
└── 04-validate/          # Validation reports
```

## Dependencies

- streamlit >= 1.28.0
- scikit-learn >= 1.3.0
- shap >= 0.44.0
- ortools >= 9.8.0
- numpy >= 1.24.0
- pandas >= 2.0.0
