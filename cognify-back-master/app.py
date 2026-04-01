# app.py — Cognify ML Service (Production Ready)
# Deploy on Railway with:
#   uvicorn app:app --host 0.0.0.0 --port $PORT

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import os

from inference.risk_engine import RiskEngine
from inference.response_builder import ResponseBuilder
from utils.logger import get_logger

logger = get_logger()

app = FastAPI(title="Cognify ML Service", version="1.0.0")

# ─── Load models once at startup ─────────────────────────────────────────────
engine = RiskEngine(calibration_path="models/calibration_params.json")
builder = ResponseBuilder()

# ─── Request schema ───────────────────────────────────────────────────────────
class AssessRequest(BaseModel):
    user_id: str
    age: int
    sex: str          # "male" | "female"
    records: List[Dict[str, Any]]

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/assess-risk")
def assess_risk(req: AssessRequest):
    try:
        # Step 1: Run the full ML pipeline
        risk_result = engine.assess_risk(
            json_records=req.records,
            age=req.age,
            sex=req.sex,
            user_id=req.user_id,
        )
        # Step 2: Format into the structured response
        response = builder.build_response(risk_assessment=risk_result)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Internal ML error")

# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,    # disabled for production
    )
