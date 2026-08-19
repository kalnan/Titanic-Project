import axios from "axios";

// Set REACT_APP_API_URL in the environment (Render dashboard, or a local .env
// file) to point at the deployed FastAPI backend. Falls back to localhost for
// local development against `uvicorn app:app --reload`.
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

export async function predictSurvival(passenger) {
  const { data } = await client.post("/predict", passenger);
  return data;
}

export async function getMetadata() {
  const { data } = await client.get("/metadata");
  return data;
}

export async function checkHealth() {
  const { data } = await client.get("/health");
  return data;
}

export default client;
