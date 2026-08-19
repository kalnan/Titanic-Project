"""
Titanic Survival Prediction API
================================
FastAPI backend that loads the XGBoost model (and preprocessing artifacts)
trained in notebooks/Titanic_Survival_Prediction.ipynb and serves predictions
to the React frontend.

Run locally:
    uvicorn app:app --reload --port 8000

Run in production (Render, via gunicorn + uvicorn workers):
    gunicorn app:app -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py
"""
import json
import os
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

# ---------------------------------------------------------------------------
# Load model + preprocessing artifacts once at startup
# ---------------------------------------------------------------------------
xgb_model = joblib.load(MODELS_DIR / "titanic_xgb_model.pkl")
label_encoders = joblib.load(MODELS_DIR / "label_encoders.pkl")

with open(MODELS_DIR / "metadata.json") as f:
    METADATA = json.load(f)

FEATURES = METADATA["features"]
TITLE_MAP = METADATA["title_map"]
VALID_TITLES = set(label_encoders["title"].classes_)
VALID_DECKS = set(label_encoders["deck"].classes_)
VALID_EMBARKED = set(label_encoders["embarked"].classes_)
VALID_AGE_GROUPS = set(label_encoders["age_group"].classes_)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Titanic Survival Prediction API",
    description="Predicts whether a Titanic passenger would have survived, "
                 "based on the model trained in the accompanying notebook.",
    version="1.0.0",
)

# Allow the React frontend (local dev + your deployed Render frontend URL) to call this API.
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class PassengerInput(BaseModel):
    pclass: int = Field(..., ge=1, le=3, description="Ticket class: 1, 2, or 3")
    sex: str = Field(..., description="'male' or 'female'")
    age: float = Field(..., ge=0, le=100, description="Age in years")
    sibsp: int = Field(0, ge=0, le=10, description="# siblings/spouses aboard")
    parch: int = Field(0, ge=0, le=10, description="# parents/children aboard")
    fare: float = Field(..., ge=0, description="Ticket fare")
    embarked: str = Field("S", description="Port of embarkation: C, Q, or S")
    title: str = Field("Mr", description="Honorific, e.g. Mr, Mrs, Miss, Master, Officer, Royalty, Other")
    cabin: Optional[str] = Field(None, description="Cabin code, e.g. 'C85' (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "pclass": 1,
                "sex": "female",
                "age": 29,
                "sibsp": 0,
                "parch": 0,
                "fare": 211.34,
                "embarked": "S",
                "title": "Miss",
                "cabin": "B5",
            }
        }


class PredictionResponse(BaseModel):
    survived: int
    survival_probability: float
    label: str


# ---------------------------------------------------------------------------
# Feature engineering (mirrors the notebook exactly)
# ---------------------------------------------------------------------------
def _age_group(age: float) -> str:
    if age <= 12:
        return "Child"
    if age <= 19:
        return "Teen"
    if age <= 35:
        return "YoungAdult"
    if age <= 60:
        return "Adult"
    return "Senior"


def _safe_encode(encoder, value: str, field_name: str) -> int:
    if value not in encoder.classes_:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid value '{value}' for '{field_name}'. "
                   f"Expected one of: {sorted(encoder.classes_.tolist())}",
        )
    return int(encoder.transform([value])[0])


def build_feature_row(p: PassengerInput) -> pd.DataFrame:
    sex = p.sex.strip().lower()
    if sex not in ("male", "female"):
        raise HTTPException(status_code=422, detail="'sex' must be 'male' or 'female'")

    title = TITLE_MAP.get(p.title, p.title)
    if title not in VALID_TITLES:
        title = "Other"

    embarked = p.embarked.strip().upper()
    if embarked not in VALID_EMBARKED:
        raise HTTPException(status_code=422, detail=f"'embarked' must be one of {sorted(VALID_EMBARKED)}")

    family_size = p.sibsp + p.parch + 1
    has_cabin = int(bool(p.cabin))
    deck = p.cabin[0].upper() if p.cabin else "U"
    if deck not in VALID_DECKS:
        deck = "U"
    fare_per_person = p.fare / family_size if family_size > 0 else p.fare
    age_group = _age_group(p.age)

    row = {
        "pclass": p.pclass,
        "sex": _safe_encode(label_encoders["sex"], sex, "sex"),
        "age": p.age,
        "sibsp": p.sibsp,
        "parch": p.parch,
        "fare": p.fare,
        "embarked": _safe_encode(label_encoders["embarked"], embarked, "embarked"),
        "title": _safe_encode(label_encoders["title"], title, "title"),
        "family_size": family_size,
        "is_alone": int(family_size == 1),
        "has_cabin": has_cabin,
        "deck": _safe_encode(label_encoders["deck"], deck, "deck"),
        "fare_per_person": fare_per_person,
        "age_group": _safe_encode(label_encoders["age_group"], age_group, "age_group"),
    }
    return pd.DataFrame([row])[FEATURES]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Titanic Survival Prediction API is running.",
        "docs": "/docs",
        "model": METADATA.get("production_model"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metadata")
def metadata():
    return METADATA


@app.post("/predict", response_model=PredictionResponse)
def predict(passenger: PassengerInput):
    X = build_feature_row(passenger)
    proba = float(xgb_model.predict_proba(X)[0, 1])
    survived = int(proba > 0.5)
    return PredictionResponse(
        survived=survived,
        survival_probability=round(proba, 4),
        label="Survived" if survived == 1 else "Did not survive",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
