import React, { useState } from "react";
import { predictSurvival } from "../api/api";

const initialState = {
  pclass: 1,
  sex: "female",
  age: 29,
  sibsp: 0,
  parch: 0,
  fare: 100,
  embarked: "S",
  title: "Miss",
  cabin: "",
};

export default function PredictionForm() {
  const [form, setForm] = useState(initialState);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: ["pclass", "age", "sibsp", "parch", "fare"].includes(name)
        ? Number(value)
        : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = { ...form, cabin: form.cabin || null };
      const data = await predictSurvival(payload);
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.detail
          ? JSON.stringify(err.response.data.detail)
          : "Something went wrong calling the prediction API."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <form onSubmit={handleSubmit} className="form">
        <div className="form-row">
          <label>
            Class
            <select name="pclass" value={form.pclass} onChange={handleChange}>
              <option value={1}>1st</option>
              <option value={2}>2nd</option>
              <option value={3}>3rd</option>
            </select>
          </label>

          <label>
            Sex
            <select name="sex" value={form.sex} onChange={handleChange}>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
          </label>

          <label>
            Title
            <select name="title" value={form.title} onChange={handleChange}>
              {["Mr", "Mrs", "Miss", "Master", "Officer", "Royalty", "Other"].map(
                (t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                )
              )}
            </select>
          </label>
        </div>

        <div className="form-row">
          <label>
            Age
            <input type="number" name="age" min="0" max="100" value={form.age} onChange={handleChange} />
          </label>

          <label>
            Siblings / Spouses aboard
            <input type="number" name="sibsp" min="0" max="10" value={form.sibsp} onChange={handleChange} />
          </label>

          <label>
            Parents / Children aboard
            <input type="number" name="parch" min="0" max="10" value={form.parch} onChange={handleChange} />
          </label>
        </div>

        <div className="form-row">
          <label>
            Fare
            <input type="number" name="fare" min="0" step="0.01" value={form.fare} onChange={handleChange} />
          </label>

          <label>
            Embarked
            <select name="embarked" value={form.embarked} onChange={handleChange}>
              <option value="S">Southampton</option>
              <option value="C">Cherbourg</option>
              <option value="Q">Queenstown</option>
            </select>
          </label>

          <label>
            Cabin (optional)
            <input type="text" name="cabin" placeholder="e.g. C85" value={form.cabin} onChange={handleChange} />
          </label>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Predict Survival"}
        </button>
      </form>

      {error && <div className="result error">{error}</div>}

      {result && (
        <div className={`result ${result.survived ? "survived" : "died"}`}>
          <h3>{result.label}</h3>
          <p>Survival probability: {(result.survival_probability * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}
