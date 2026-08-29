"""
Day 4 — Action Recommendations Engine
=========================================
Explicit, rule-based (NOT ML-driven) action recommendations.

Produced by deterministic rules over:
  - risk_level     (LOW / MEDIUM / HIGH)
  - exposure       (population, critical infrastructure flags)
  - priority_level (LOW / MEDIUM / HIGH / CRITICAL)
  - response_gap   (0–1 float)

Authority remains the decision-maker.
These are RECOMMENDATIONS, not autonomous commands.
"""


def generate_actions(
    risk_level: str,
    priority_level: str,
    response_gap_score: float,
    has_critical_road: bool = False,
    has_hospital: bool = False,
    has_school: bool = False,
    population: int = 0,
    available_volunteers: int = 0,
) -> list[str]:
    actions: list[str] = []

    rl = risk_level.upper()
    pl = priority_level.upper()

    # ── Critical / High risk actions ──────────────────────────────────────────
    if rl == "HIGH" or pl in ("CRITICAL", "HIGH"):
        actions.append("Alert local District Disaster Management Authority (DDMA)")
        if population > 500:
            actions.append("Initiate pre-emptive evacuation planning for high-density zone")
        elif population > 100:
            actions.append("Prepare evacuation resources and pre-position rescue teams")
        if has_critical_road:
            actions.append("Monitor and consider restricting critical road access")
        if has_hospital:
            actions.append("Coordinate hospital evacuation readiness and patient transfer plan")
        if has_school:
            actions.append("Notify schools — initiate precautionary early dismissal if warranted")

    # ── Response gap actions ───────────────────────────────────────────────────
    if response_gap_score >= 0.7:
        actions.append("Request additional response resources from neighbouring districts")
        if available_volunteers == 0:
            actions.append("No volunteers currently available — escalate to SDMA for deployment")
    elif response_gap_score >= 0.4:
        actions.append("Mobilise available volunteers to standby positions near the affected area")

    # ── Medium risk actions ────────────────────────────────────────────────────
    if rl == "MEDIUM" and pl not in ("CRITICAL", "HIGH"):
        actions.append("Increase monitoring frequency — check rainfall and stream levels every 2 hours")
        actions.append("Issue community advisory for low-lying and slope-adjacent settlements")

    # ── Low risk actions ───────────────────────────────────────────────────────
    if rl == "LOW" and pl == "LOW":
        actions.append("Continue routine monitoring")
        actions.append("No immediate intervention required")

    # ── Fallback ───────────────────────────────────────────────────────────────
    if not actions:
        actions.append("Review latest sensor data and update risk assessment")

    return actions
