"""
Unified Prediction Service
==========================
Consolidates ML inference into a single reusable service.

Loads the calibrated model once at startup and exposes a clean interface
for risk prediction with calibrated confidence and feature attributions.

Model artifact expected: landslide_calibrated_v1.joblib
  - Binary classifier (landslide: 0/1)
  - Output: predict_proba(X)[:, 1] → probability of landslide
  - Confidence derived from calibrated probability, not a constant.
"""
import os
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Model paths ──────────────────────────────────────────────────────────────
ML_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml")
MODEL_FILE = os.path.join(ML_DIR, "models", "landslide_calibrated_v1.joblib")
THRESHOLD_FILE = os.path.join(ML_DIR, "models", "landslide_final_threshold.json")

# ─── Feature order (matches training pipeline) ────────────────────────────────
FEATURES = [
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness",
]

# ─── Model feature importances (fallback if model doesn't expose them) ────────
# These reflect the relative contribution of each feature family in the
# calibrated HGB model. Used for explanation attribution when the model
# itself doesn't provide feature_importances_.
FALLBACK_IMPORTANCES = {
    "rainfall_24h": 0.22,
    "rainfall_7day": 0.15,
    "rainfall_3day": 0.12,
    "rainfall_14day": 0.08,
    "rainfall_30day": 0.05,
    "rainfall_mm": 0.05,
    "rainfall_previous_day": 0.04,
    "rainfall_2day_lag": 0.03,
    "rainfall_3day_lag": 0.02,
    "heavy_rain_flag": 0.04,
    "very_heavy_rain_flag": 0.03,
    "elevation_m": 0.06,
    "slope_deg": 0.07,
    "aspect_deg": 0.02,
    "terrain_roughness": 0.02,
}


@dataclass
class PredictionResult:
    """Result of a single risk prediction."""
    risk_score: float
    risk_level: str
    confidence: float
    model_version: str
    feature_importances: dict[str, float] = field(default_factory=dict)
    top_drivers: list[str] = field(default_factory=list)
    early_warning: bool = False
    threshold: float = 0.30


class PredictionService:
    """
    Singleton ML prediction service.
    Loads the calibrated model once and serves predictions on demand.
    """

    def __init__(self):
        self._model = None
        self._threshold = 0.30
        self._model_version = "landslide_calibrated_v1"
        self._loaded = False
        self._feature_importances: dict[str, float] = {}

    def load(self) -> bool:
        """Load model and threshold from disk. Returns True if successful."""
        try:
            import joblib
        except ImportError:
            logger.warning("[PREDICTION_SERVICE] joblib not installed — prediction unavailable")
            return False

        if not os.path.exists(MODEL_FILE):
            logger.warning("[PREDICTION_SERVICE] Model file not found: %s", MODEL_FILE)
            return False

        try:
            artifact = joblib.load(MODEL_FILE)

            # Extract model from various artifact formats
            if isinstance(artifact, dict):
                if "model" in artifact:
                    self._model = artifact["model"]
                elif "calibrated_model" in artifact:
                    self._model = artifact["calibrated_model"]
                else:
                    self._model = None
                    for key, value in artifact.items():
                        if hasattr(value, "predict_proba"):
                            self._model = value
                            logger.info("[PREDICTION_SERVICE] Using model from key: %s", key)
                            break
            else:
                self._model = artifact

            if self._model is None:
                logger.error("[PREDICTION_SERVICE] Could not extract model from artifact")
                return False

            # Extract feature importances if available
            if hasattr(self._model, "feature_importances_"):
                importances = self._model.feature_importances_
                for i, fname in enumerate(FEATURES):
                    if i < len(importances):
                        self._feature_importances[fname] = float(importances[i])
                logger.info("[PREDICTION_SERVICE] Extracted feature importances from model")
            else:
                self._feature_importances = FALLBACK_IMPORTANCES.copy()
                logger.info("[PREDICTION_SERVICE] Using fallback feature importances")

        except Exception as e:
            logger.error("[PREDICTION_SERVICE] Failed to load model: %s", e)
            return False

        # Load threshold
        if os.path.exists(THRESHOLD_FILE):
            try:
                with open(THRESHOLD_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._threshold = float(
                        data.get("threshold", data.get("final_threshold", data.get("decision_threshold", 0.30)))
                    )
                elif isinstance(data, (int, float)):
                    self._threshold = float(data)
            except Exception:
                logger.warning("[PREDICTION_SERVICE] Could not read threshold, using default 0.30")

        self._loaded = True
        logger.info(
            "[PREDICTION_SERVICE] Model loaded: %s, threshold: %.2f",
            type(self._model).__name__,
            self._threshold,
        )
        return True

    @property
    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    def predict(
        self,
        rainfall_24h: float = 0.0,
        rainfall_3day: float = 0.0,
        rainfall_7day: float = 0.0,
        rainfall_14day: float = 0.0,
        rainfall_30day: float = 0.0,
        elevation_m: float = 0.0,
        slope_deg: float = 0.0,
        aspect_deg: float = 0.0,
        terrain_roughness: float = 0.0,
        rainfall_previous_day: float = 0.0,
        rainfall_2day_lag: float = 0.0,
        rainfall_3day_lag: float = 0.0,
        rainfall_mm: Optional[float] = None,
    ) -> Optional[PredictionResult]:
        """
        Run calibrated model inference.
        Returns PredictionResult or None if model unavailable.
        """
        if not self.is_available:
            return None

        try:
            import numpy as np
            import pandas as pd
        except ImportError:
            logger.warning("[PREDICTION_SERVICE] numpy/pandas not installed")
            return None

        if rainfall_mm is None:
            rainfall_mm = rainfall_24h

        heavy_rain_flag = int(float(rainfall_24h) >= 64.5)
        very_heavy_rain_flag = int(float(rainfall_24h) >= 115.6)

        X = pd.DataFrame([{
            "rainfall_mm": float(rainfall_mm),
            "rainfall_24h": float(rainfall_24h),
            "rainfall_3day": float(rainfall_3day),
            "rainfall_7day": float(rainfall_7day),
            "rainfall_14day": float(rainfall_14day),
            "rainfall_30day": float(rainfall_30day),
            "rainfall_previous_day": float(rainfall_previous_day),
            "rainfall_2day_lag": float(rainfall_2day_lag),
            "rainfall_3day_lag": float(rainfall_3day_lag),
            "heavy_rain_flag": heavy_rain_flag,
            "very_heavy_rain_flag": very_heavy_rain_flag,
            "elevation_m": float(elevation_m),
            "slope_deg": float(slope_deg),
            "aspect_deg": float(aspect_deg),
            "terrain_roughness": float(terrain_roughness),
        }])

        X = X[FEATURES]

        if X.isnull().any().any():
            logger.warning("[PREDICTION_SERVICE] NULL values in input, cannot predict")
            return None

        try:
            probabilities = self._model.predict_proba(X)
            probability = float(probabilities[0][1])
            probability = max(0.0, min(1.0, probability))
        except Exception as e:
            logger.error("[PREDICTION_SERVICE] Prediction failed: %s", e)
            return None

        # Risk level classification (consistent with live_risk.py thresholds)
        if probability >= 0.60:
            risk_level = "HIGH"
        elif probability >= 0.30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Confidence from calibrated probability
        # Calibrated models produce well-calibrated probabilities,
        # so the probability itself IS the confidence estimate.
        # We use the probability as the confidence signal:
        # - High probability → high confidence in risk
        # - Mid probability → moderate confidence
        # - Low probability → high confidence in no-risk
        confidence = round(max(probability, 1.0 - probability), 4)

        # Top drivers by feature importance
        sorted_importances = sorted(
            self._feature_importances.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        top_drivers = [name for name, _ in sorted_importances[:5]]

        return PredictionResult(
            risk_score=round(probability, 6),
            risk_level=risk_level,
            confidence=confidence,
            model_version=self._model_version,
            feature_importances=self._feature_importances,
            top_drivers=top_drivers,
            early_warning=probability >= self._threshold,
            threshold=self._threshold,
        )


# ─── Module-level singleton ───────────────────────────────────────────────────
prediction_service = PredictionService()
