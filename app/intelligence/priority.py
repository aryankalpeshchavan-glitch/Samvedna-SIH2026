"""
Day 4 — Operational Priority Engine
=====================================
Computes an explainable priority score from:
  1. ML Risk Score       (weight: W_RISK)
  2. Exposure Score      (weight: W_EXPOSURE)
  3. Vulnerability Score (weight: W_VULNERABILITY)
  4. Response Gap        (weight: W_RESPONSE_GAP)

Formula:
  priority_score = (
      W_RISK * risk_score
    + W_EXPOSURE * exposure_score
    + W_VULNERABILITY * vulnerability_score
    + W_RESPONSE_GAP * response_gap_score
  )  * 100   [clamped to 0–100]

All weights configurable via environment.

This is an explicit, rule-based, explainable function — NOT an ML model.
"""
import math
import os
from typing import Optional


# ─── Configurable weights ─────────────────────────────────────────────────────
W_RISK           = float(os.getenv("PRIORITY_W_RISK",           "0.35"))
W_EXPOSURE       = float(os.getenv("PRIORITY_W_EXPOSURE",       "0.30"))
W_VULNERABILITY  = float(os.getenv("PRIORITY_W_VULNERABILITY",  "0.20"))
W_RESPONSE_GAP   = float(os.getenv("PRIORITY_W_RESPONSE_GAP",   "0.15"))


# ─── Exposure scoring ─────────────────────────────────────────────────────────
def compute_exposure_score(
    population: int = 0,
    households: int = 0,
    schools: int = 0,
    hospitals: int = 0,
    critical_roads: int = 0,
) -> float:
    """
    Normalised 0–1 score expressing how much is at risk.
    Weights applied to each factor reflect the relative importance
    of human life vs infrastructure in disaster response.

    Population cap at 5000 for normalisation (NER context).
    """
    pop_score   = min(1.0, population / 5000.0)
    hh_score    = min(1.0, households / 1500.0)
    school_score = min(1.0, schools    / 5.0)
    hosp_score   = min(1.0, hospitals  / 3.0)
    road_score   = min(1.0, critical_roads / 3.0)

    return round(
        0.40 * pop_score
        + 0.25 * hh_score
        + 0.15 * school_score
        + 0.10 * hosp_score
        + 0.10 * road_score,
        4,
    )


# ─── Vulnerability scoring ────────────────────────────────────────────────────
def compute_vulnerability_score(
    distance_to_nearest_hospital_km: Optional[float] = None,
    has_early_warning: bool = False,
    road_access_quality: str = "moderate",   # good | moderate | poor
) -> float:
    """
    Normalised 0–1 score expressing how badly prepared / connected a community is.
    """
    # Hospital access: >50 km → very vulnerable
    if distance_to_nearest_hospital_km is None:
        hosp_vuln = 0.5
    else:
        hosp_vuln = min(1.0, distance_to_nearest_hospital_km / 50.0)

    warning_vuln = 0.0 if has_early_warning else 0.5

    road_vuln_map = {"good": 0.1, "moderate": 0.5, "poor": 1.0}
    road_vuln = road_vuln_map.get(road_access_quality, 0.5)

    return round(
        0.40 * hosp_vuln + 0.30 * warning_vuln + 0.30 * road_vuln,
        4,
    )


# ─── Response gap scoring ─────────────────────────────────────────────────────
def compute_response_gap_score(
    available_volunteers: int,
    nearby_resources: int,
    incident_severity: int = 1,  # 1–5
) -> float:
    """
    0 = full response available, 1 = no response capacity.
    Severity is from the incident model (1–5).
    """
    demand = incident_severity  # 1–5
    supply = min(available_volunteers + nearby_resources, 10)  # cap at 10
    if supply == 0:
        return 1.0
    ratio = demand / max(supply, 1)
    return round(min(1.0, ratio), 4)


# ─── Priority level label ─────────────────────────────────────────────────────
def priority_level(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


# ─── Main entry point ─────────────────────────────────────────────────────────
def compute_priority(
    risk_score: float,
    exposure_score: float,
    vulnerability_score: float,
    response_gap_score: float,
) -> dict:
    raw = (
        W_RISK          * risk_score
        + W_EXPOSURE      * exposure_score
        + W_VULNERABILITY * vulnerability_score
        + W_RESPONSE_GAP  * response_gap_score
    )
    score = round(min(100.0, raw * 100), 1)
    return {
        "priority_score": score,
        "priority_level": priority_level(score),
        "weights": {
            "risk": W_RISK,
            "exposure": W_EXPOSURE,
            "vulnerability": W_VULNERABILITY,
            "response_gap": W_RESPONSE_GAP,
        },
        "factors": {
            "risk": round(risk_score, 4),
            "exposure": round(exposure_score, 4),
            "vulnerability": round(vulnerability_score, 4),
            "response_gap": round(response_gap_score, 4),
        },
    }
