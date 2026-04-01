Project Architecture
health_drift_system
│
├── data/                  # Data schemas + synthetic generator
├── preprocessing/         # Data cleaning & feature engineering
├── models/                # Drift + risk models
├── inference/             # Final risk engine
├── training/              # Model calibration scripts
├── utils/                 # Config, logging, constants
│
├── test_inference.py      # End-to-end pipeline test
└── models/calibration_params.json 


Pipeline Overview
Raw wearable data
        ↓
JSON parsing
        ↓
Daily aggregation
        ↓
Missing value handling
        ↓
Demographic normalization
        ↓
Rolling slope computation
        ↓
Drift estimation
        ↓
Anomaly detection
        ↓
Domain risk aggregation
        ↓
Logistic regression calibration
        ↓
Final risk assessment

Installation
git clone https://github.com/Aryan-sriii/cognify-back.git
cd cognify-back

Create virtual environment:
python -m venv venv
source venv/bin/activate

Install dependencies:
pip install -r requirements.tx

Running the Engine
python test_inference.py

Backend Integration

The backend should interact with the RiskEngine class.

Location:

inference/risk_engine.py

Import:

from inference.risk_engine import RiskEngine

Initialize:

engine = RiskEngine(
    calibration_path="models/calibration_params.json"
)
Required Input Format

The engine expects JSON records representing daily health metrics.

Example input:

[
  {
    "timestamp": "2026-03-01",
    "userId": "USER_001",
    "steps": 8300,
    "heartRateAvg": 71,
    "hrvSdnnMs": 42,
    "bloodOxygenAvg": 98,
    "gaitSpeedMs": 1.25,
    "deepSleepHours": 1.5,
    "remSleepHours": 1.7,
    "reactionTimeMs": 280,
    "memoryScore": 0.87
  }
]

Backend should pass this list to:

result = engine.assess_risk(
    json_records=records,
    age=55,
    sex="male",
    user_id="USER_001"
)
Output Format

The engine returns a structured risk assessment.

Example response:

{
  "user_id": "USER_001",
  "stability_index": 0.54,
  "decline_probability": 0.28,
  "domain_risks": {
    "Neuro": 0.63,
    "Cardio": 0.41,
    "Frailty": 0.52
  },
  "domain_drifts": {
    "Neuro": 1.21,
    "Cardio": 0.44,
    "Frailty": 0.73
  },
  "anomalies": [],
  "data_days": 365,
  "features_used": 9
}
Recommended Backend API Endpoint

Example API endpoint:

POST /assess-risk

Request body:

{
  "user_id": "USER_001",
  "age": 55,
  "sex": "male",
  "records": [...]
}

Backend handler example:

engine = RiskEngine()

def assess_user(data):

    result = engine.assess_risk(
        json_records=data["records"],
        age=data["age"],
        sex=data["sex"],
        user_id=data["user_id"]
    )

    return result
Key Output Metrics
Metric	Meaning
Stability Index	Overall system health stability
Decline Probability	Risk of health decline
Domain Risks	Risk by health domain
Domain Drifts	Rate of health change
Anomalies	Detected unusual events
Current Model Type

Drift-based longitudinal analysis

Domain hazard transformation

Logistic regression calibration

Multi-scale slope estimation

Notes for Backend Integration

Engine expects daily aggregated data

Minimum recommended data length: 60 days

Optimal performance: 180–365 days

Missing values are handled automatically

Results are returned as JSON-serializable dictionary

Future Improvements

GPU accelerated slope computation

Real-time streaming inference

Clinical calibration with real datasets

Expanded domain models

Maintainers

Cognify Research Team

After creating it run:

git add README.md
git commit -m "Add backend integration README"
git push
