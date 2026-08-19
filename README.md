# 🚢 Titanic Survival Prediction

An end-to-end ML/DL project: a research notebook that cleans the raw Titanic
export, engineers features, trains and compares 4 models (Logistic
Regression, Random Forest, XGBoost, and a PyTorch deep-learning MLP), and a
full-stack web app (FastAPI backend + React frontend) that serves live
predictions from the trained model.

## Repository structure

```
titanic-survival-prediction/
├── notebooks/
│   ├── Titanic_Survival_Prediction.ipynb   # full research notebook (executed, with outputs)
│   └── Titanic_Research_v6.csv             # source dataset
├── backend/                                # FastAPI service — deploy independently on Render
│   ├── app.py
│   ├── gunicorn_conf.py
│   ├── Procfile
│   ├── requirements.txt
│   ├── runtime.txt
│   ├── .env.example
│   └── models/                             # artifacts exported by the notebook
│       ├── titanic_xgb_model.pkl           # production model
│       ├── titanic_rf_model.pkl
│       ├── titanic_logreg_model.pkl
│       ├── titanic_dl_model.pt
│       ├── scaler.pkl
│       ├── label_encoders.pkl
│       └── metadata.json
├── frontend/                               # React app — deploy independently on Render
│   ├── package.json
│   ├── public/index.html
│   ├── src/
│   │   ├── App.js / App.css / index.js
│   │   ├── components/PredictionForm.js
│   │   └── api/api.js
│   └── .env.example
├── render.yaml                             # one-click Render blueprint for both services
└── .gitignore
```

Backend and frontend are **fully separate** apps (own `package.json` /
`requirements.txt`), so each can be built, containerized, and deployed to
Render independently.

## Data & modelling summary

The raw CSV had two real data-quality issues, both documented and fixed in
the notebook:
- `age` used a comma as the decimal separator (locale export artifact).
- `fare` used `.` as both a thousands separator and the decimal point.

`boat` and `body` were dropped as **leakage columns** (they only exist as a
*consequence* of survival). After cleaning + feature engineering (title,
family size, deck, fare-per-person, age group, etc.), four models were
trained and compared on a held-out 20% test split:

| Model | Accuracy | ROC-AUC |
|---|---|---|
| Logistic Regression | ~0.84 | ~0.87 |
| Random Forest | ~0.85 | ~0.89 |
| **XGBoost (deployed)** | ~0.84 | **~0.89** |
| Deep Learning (PyTorch MLP) | ~0.82 | ~0.89 |

XGBoost is deployed to the API: strong performance, no scaling required, and
a tiny artifact with no heavy runtime dependency.

Open `notebooks/Titanic_Survival_Prediction.ipynb` for the full walkthrough
(EDA plots, cleaning rationale, all metrics, confusion matrices, ROC curves,
feature importances, and business conclusions).

## Running locally

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # edit ALLOWED_ORIGINS if needed
uvicorn app:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

To run it the way it runs in production (gunicorn + uvicorn workers):

```bash
gunicorn app:app -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py
```

### 2. Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env      # set REACT_APP_API_URL=http://localhost:8000 for local dev
npm start
```

Opens at `http://localhost:3000` and calls the backend at
`REACT_APP_API_URL` (defaults to `http://localhost:8000` if unset).

## Deploying to Render

You can deploy with the included `render.yaml` blueprint (New → Blueprint,
point it at this repo) which creates both services, **or** set each up
manually:

### Backend — Web Service
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py`
- Env var: `ALLOWED_ORIGINS=https://<your-frontend>.onrender.com`

### Frontend — Static Site
- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Publish directory: `build`
- Env var: `REACT_APP_API_URL=https://<your-backend>.onrender.com`
- Add a rewrite rule `/* → /index.html` (included in `render.yaml`) so
  client-side routing works.

After both are live, update each service's env var to point at the other's
real Render URL and redeploy.

## API reference

`POST /predict`

```json
{
  "pclass": 1,
  "sex": "female",
  "age": 29,
  "sibsp": 0,
  "parch": 0,
  "fare": 211.34,
  "embarked": "S",
  "title": "Miss",
  "cabin": "B5"
}
```

Response:

```json
{
  "survived": 1,
  "survival_probability": 0.9333,
  "label": "Survived"
}
```

Other endpoints: `GET /health`, `GET /metadata`, interactive docs at `/docs`.
