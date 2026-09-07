package com.crisiscore.app.data.local

import com.crisiscore.app.data.model.RiskZone

object SyntheticRiskData {

    fun zones(): List<RiskZone> = listOf(
        RiskZone("rz-01", "Machkhowa Riverfront", 26.1450, 91.7450, 89.0, "CRITICAL", "synthetic"),
        RiskZone("rz-02", "Pandu Port Bank", 26.1833, 91.6920, 86.0, "CRITICAL", "synthetic"),
        RiskZone("rz-03", "Uzan Bazar Riverbank", 26.1896, 91.6877, 82.0, "CRITICAL", "synthetic"),
        RiskZone("rz-04", "Chandmari Hill Base", 26.1369, 91.8225, 78.0, "HIGH", "synthetic"),
        RiskZone("rz-05", "Zoo Road Slope", 26.1240, 91.7950, 74.0, "HIGH", "synthetic"),
        RiskZone("rz-06", "Palashbari Escarpment", 26.1480, 91.6600, 71.0, "HIGH", "synthetic"),
        RiskZone("rz-07", "Dispur Catchment", 26.1620, 91.7980, 62.0, "MEDIUM", "synthetic"),
        RiskZone("rz-08", "Six Mile Lowland", 26.1076, 91.7604, 55.0, "MEDIUM", "synthetic"),
        RiskZone("rz-09", "Khanapara Hill Road", 26.0833, 91.7900, 41.0, "WATCH", "synthetic"),
        RiskZone("rz-10", "Fancy Bazar", 26.1730, 91.6980, 28.0, "LOW", "synthetic"),
        RiskZone("rz-11", "Beltola", 26.1200, 91.8200, 22.0, "LOW", "synthetic"),
    )
}