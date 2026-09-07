import React from 'react';
import useStore from '../../store/useStore';

export default function PredictionCard() {
  const setShowPrediction = useStore((s) => s.setShowPrediction);

  return (
    <div className="prediction-card" id="prediction-card">
      <button className="prediction-close" onClick={() => setShowPrediction(false)}>✕</button>
      <div className="prediction-card-title">
        <span className="badge badge-high">HIGH</span>
        AI Prediction Summary
        <span style={{ marginLeft: 'auto', fontSize: 10, opacity: 0.7, fontFamily: 'monospace' }}>[Demo Scenario]</span>
      </div>

      <div className="prediction-stat">
        <span className="prediction-stat-label">Risk Probability</span>
        <span className="prediction-stat-value">91%</span>
      </div>
      <div className="prediction-stat">
        <span className="prediction-stat-label">Trigger Rainfall</span>
        <span className="prediction-stat-value">142 mm / 6hrs</span>
      </div>
      <div className="prediction-stat">
        <span className="prediction-stat-label">Affected Population</span>
        <span className="prediction-stat-value">~240 persons</span>
      </div>
      <div className="prediction-stat">
        <span className="prediction-stat-label">Impact Area</span>
        <span className="prediction-stat-value">12.4 km²</span>
      </div>
      <div className="prediction-stat">
        <span className="prediction-stat-label">Confidence</span>
        <span className="prediction-stat-value">91%</span>
      </div>
      <div className="prediction-stat">
        <span className="prediction-stat-label">Model</span>
        <span className="prediction-stat-value">XGBoost 24h (NER)</span>
      </div>

      <div style={{ marginTop: 12, fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
        Simulation scenario based on sustained rainfall exceeding threshold,
        saturated soil, and ground tilt detected at ridge stations.
      </div>
    </div>
  );
}
