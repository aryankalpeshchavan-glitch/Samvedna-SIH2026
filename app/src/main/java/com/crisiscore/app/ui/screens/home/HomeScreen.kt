package com.crisiscore.app.ui.screens.home

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.*
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.components.TabType
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    repository: CrisisCoreRepository,
    onTriggerSos: () -> Unit,
    onNavigate: (TabType) -> Unit,
    onAuthClick: () -> Unit = {}
) {
    val scope = rememberCoroutineScope()
    val haptic = LocalHapticFeedback.current
    var location by remember { mutableStateOf<LocationData?>(null) }
    var isEmergencyMode by remember { mutableStateOf(false) }
    var riskZones by remember { mutableStateOf<List<RiskZone>>(emptyList()) }
    var decision by remember { mutableStateOf<DecisionResponse?>(null) }
    var isLoadingIntelligence by remember { mutableStateOf(true) }
    var showWhyRiskDialog by remember { mutableStateOf(false) }
    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        repository.ensureAuthenticated()
        val loc = repository.getCurrentLocation()
        location = loc
        val lat = loc.latitude ?: 26.1445
        val lng = loc.longitude ?: 91.7362
        riskZones = repository.getRiskZones("24h")
        decision = repository.getDecision(lat, lng)
        isLoadingIntelligence = false
    }

    val pulseAnim = rememberInfiniteTransition(label = "pulse")
    val pulseAlpha by pulseAnim.animateFloat(
        initialValue = 0.85f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseAlpha"
    )
    val pulseScale by pulseAnim.animateFloat(
        initialValue = 1f,
        targetValue = 1.02f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseScale"
    )

    if (showWhyRiskDialog && decision != null) {
        AlertDialog(
            onDismissRequest = { showWhyRiskDialog = false },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Psychology, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("Risk Assessment Explanation", style = MaterialTheme.typography.titleMedium)
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(
                        decision?.explanation?.summary ?: "Risk level is derived from regional rainfall, slope stability, and real-time ground sensors.",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.SemiBold
                    )

                    decision?.explanation?.narrative?.let {
                        Text(it, style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                    }

                    if (!decision?.risk?.top_drivers.isNullOrEmpty()) {
                        Text("Top Drivers:", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold, color = PrimaryGreen)
                        for (driver in decision?.risk?.top_drivers.orEmpty()) {
                            Text("\u2022 $driver", style = MaterialTheme.typography.bodySmall)
                        }
                    }

                    if (!decision?.actions.isNullOrEmpty()) {
                        Text("Recommended Actions:", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold, color = WarningAmber)
                        for (action in decision?.actions.orEmpty()) {
                            Text("\u2192 $action", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showWhyRiskDialog = false }) {
                    Text("Understood", color = PrimaryGreen, fontWeight = FontWeight.Bold)
                }
            }
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        if (isEmergencyMode) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = EmergencyRed)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(Icons.Filled.Warning, null, tint = CanvasLight, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("EVACUATION MODE ACTIVE", color = CanvasLight, fontWeight = FontWeight.Black, fontSize = 14.sp)
                        Text("Navigate to nearest safe shelter", color = CanvasLight.copy(alpha = 0.8f), fontSize = 11.sp)
                    }
                }
            }
        }

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MapBackground)
        ) {
            CrisisMapView(
                location = location,
                riskZones = riskZones,
                isEmergencyMode = isEmergencyMode,
                onMyLocationClick = {
                    scope.launch {
                        isLoadingIntelligence = true
                        val loc = repository.getCurrentLocation()
                        location = loc
                        val lat = loc.latitude ?: 26.1445
                        val lng = loc.longitude ?: 91.7362
                        decision = repository.getDecision(lat, lng)
                        isLoadingIntelligence = false
                    }
                },
                onEmergencyToggle = { isEmergencyMode = !isEmergencyMode }
            )
        }

        // Live Risk Intelligence Card
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            borderColor = when (decision?.risk?.risk_level?.uppercase()) {
                "CRITICAL" -> EmergencyRed.copy(alpha = 0.6f)
                "HIGH" -> WarningAmber.copy(alpha = 0.6f)
                else -> PrimaryGreen.copy(alpha = 0.4f)
            }
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Analytics, null, tint = PrimaryGreen, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("LIVE SECTOR RISK ASSESSMENT", style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 1.sp), color = PrimaryGreen, fontWeight = FontWeight.Bold)
                }
                DataSourceBadge("live")
            }

            Spacer(Modifier.height(8.dp))

            if (isLoadingIntelligence) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(16.dp), color = PrimaryGreen, strokeWidth = 2.dp)
                    Spacer(Modifier.width(8.dp))
                    Text("Fetching real-time intelligence...", style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
            } else {
                val currentRisk = decision?.risk
                val riskLevel = currentRisk?.risk_level ?: "MODERATE"
                val score = currentRisk?.risk_score ?: 0.45
                val sectorName = location?.addressName ?: decision?.location_id?.ifBlank { null } ?: "Guwahati / Assam Sector"
                val latVal = decision?.lat ?: location?.latitude ?: 26.1445
                val lngVal = decision?.lng ?: location?.longitude ?: 91.7362

                // Geographic Location Identifier
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Filled.Place, null, tint = PrimaryGreen, modifier = Modifier.size(14.dp))
                    Spacer(Modifier.width(4.dp))
                    Text(
                        "$sectorName \u2022 ${String.format("%.4f\u00b0 N, %.4f\u00b0 E", latVal, lngVal)}",
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                        color = TextPrimaryLight
                    )
                }

                Spacer(Modifier.height(6.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            SeverityBadge(riskLevel)
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "Score: ${String.format("%.2f", score)}",
                                style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                                color = TextPrimaryLight
                            )
                            currentRisk?.confidence?.let { conf ->
                                Spacer(Modifier.width(6.dp))
                                Text(
                                    "(${(conf * 100).toInt()}% conf)",
                                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                                    color = TextSecondaryLight
                                )
                            }
                        }
                        if (!currentRisk?.top_drivers.isNullOrEmpty()) {
                            Spacer(Modifier.height(4.dp))
                            Text(
                                "Drivers: ${currentRisk?.top_drivers?.joinToString(", ")}",
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                                color = TextSecondaryLight
                            )
                        }
                        val freshness = decision?.computed_at?.take(19)?.replace("T", " ") ?: "Live telemetry"
                        Spacer(Modifier.height(2.dp))
                        Text(
                            "Updated: $freshness",
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                            color = TextSecondaryLight.copy(alpha = 0.8f)
                        )
                    }

                    TextButton(
                        onClick = { showWhyRiskDialog = true },
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Icon(Icons.Outlined.Info, null, modifier = Modifier.size(16.dp), tint = PrimaryGreen)
                        Spacer(Modifier.width(4.dp))
                        Text("Why Risk?", style = MaterialTheme.typography.labelSmall, color = PrimaryGreen, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Spacer(Modifier.height(10.dp))

        // CENTERED EMERGENCY SOS BUTTON (Primary Emergency Action)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(20.dp))
                .then(
                    Modifier.graphicsLayer {
                        scaleX = pulseScale
                        scaleY = pulseScale
                        alpha = pulseAlpha
                    }
                ),
            shape = RoundedCornerShape(20.dp),
            color = EmergencyRed,
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onTriggerSos()
            }
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 20.dp, horizontal = 24.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.Emergency, null, tint = CanvasLight, modifier = Modifier.size(32.dp))
                Spacer(Modifier.width(16.dp))
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        T.get("home.triggerSos"),
                        color = CanvasLight,
                        fontWeight = FontWeight.Black,
                        fontSize = 18.sp,
                        letterSpacing = 2.sp
                    )
                    Text(
                        T.get("home.sosDescription"),
                        color = CanvasLight.copy(alpha = 0.85f),
                        fontSize = 11.sp,
                        letterSpacing = 0.5.sp
                    )
                }
            }
        }

        Spacer(Modifier.height(10.dp))

        CcCard(
            modifier = Modifier.fillMaxWidth(),
            borderColor = WarningAmber.copy(alpha = 0.4f),
            backgroundColor = WarningAmber.copy(alpha = 0.05f)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.Phone, null, tint = WarningAmber, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("SMS Fallback:", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = TextPrimaryLight)
                    Text("SMS 'SOS' to 56161", style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = WarningAmber.copy(alpha = 0.12f)
                ) {
                    Text(
                        "FEATURE PHONES",
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                        color = WarningAmber,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}
