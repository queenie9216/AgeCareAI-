# AgeCareAI — Autonomous Elder Care Platform

**What it does:** Detects falls, predicts health risks, optimizes caregiver schedules, and autonomously responds to care events — all in one Streamlit app.

**Built for:** Singapore's elderly care system (1 in 4 citizens will be over 65 by 2030).

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501

## How It Works

The app has 4 AI layers. Navigate using the sidebar:

| Layer                  | What It Does                                                | How To Use                                                                                                          |
| ---------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **L1: Fall Detection** | Classifies movement as Normal Walk, Shuffle Gait, or Fall   | Select a sequence, see real-time classification. Fall + 85% confidence triggers alert.                              |
| **L2: Health Risk**    | Predicts 30-day hospital readmission risk (Low/Medium/High) | View traffic-light table sorted by risk. Click any senior to see SHAP factors explaining each prediction.           |
| **L3: Scheduler**      | Assigns caregivers to seniors using MILP optimization       | View assignments. Click "Caregiver Cancels" to remove a caregiver and watch the solver re-optimize in milliseconds. |
| **L4: Care Agent**     | Autonomous decision-making on care events                   | See pre-loaded events with AI reasoning steps. Click "Trigger Typhoon Scenario" to test crisis mode.                |

**Typhoon Integration:** L4 simultaneously calls L3's solver and executes care decisions — both update in the same second.

## Deploy to Streamlit Cloud (Free)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `app.py` → Deploy

## Project Structure

```
workspaces/AgeCareAI/
├── app.py                 # Main Streamlit app (all 4 layers)
├── requirements.txt       # Dependencies
├── .streamlit/config.toml # Streamlit settings
├── briefs/              # User requirements
├── specs/                # Technical specifications
├── 01-analysis/         # Research documents
└── 04-validate/         # Test results
```

## Tech Stack

| Component      | Technology                                   |
| -------------- | -------------------------------------------- |
| UI             | Streamlit                                    |
| Fall Detection | RandomForest on simulated accelerometer data |
| Health Risk    | XGBoost + SHAP explainability                |
| Scheduling     | OR-Tools MILP (constraint optimization)      |
| Care Agent     | Decision tree for event response             |

## Who It's For

- **Elderly patients** — immediate fall alerts, health monitoring
- **Caregivers** — optimized schedules, 24/7 alerts
- **Healthcare system** — risk-ranked worklists, reduced readmissions
