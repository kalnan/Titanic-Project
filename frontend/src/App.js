import React from "react";
import PredictionForm from "./components/PredictionForm";
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>🚢 Titanic Survival Predictor</h1>
        <p>
          Fill in a passenger's details and the trained XGBoost model
          (served by the FastAPI backend) will predict whether they
          would have survived.
        </p>
      </header>
      <main>
        <PredictionForm />
      </main>
      <footer>
        <p>Model trained in notebooks/Titanic_Survival_Prediction.ipynb</p>
      </footer>
    </div>
  );
}

export default App;
