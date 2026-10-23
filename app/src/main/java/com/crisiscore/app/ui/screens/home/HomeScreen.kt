package com.crisiscore.app.ui.screens.home

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.ui.draw.clip
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.local.SyntheticRiskData
import com.crisiscore.app.data.model.IncidentOut
import com.crisiscore.app.data.model.LocationData
import com.crisiscore.app.data.model.RiskZone
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.components.TabType
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    repository: CrisisCoreRepository,
    incidents: List<IncidentOut> = emptyList(),
    isRefreshingIncidents: Boolean = false,
    onRefreshIncidents: (() -> Unit)? = null,
    onTriggerSos: () -> Unit,
    onNavigate: (TabType) -> Unit,
    onAuthClick: () -> Unit = {}
) {
    val scope = rememberCoroutineScope()
    val haptic = LocalHapticFeedback.current
    var location by remember { mutableStateOf<LocationData?>(null) }
    var isEmergencyMode by remember { mutableStateOf(false) }
    var riskZones by remember { mutableStateOf<List<RiskZone>>(emptyList()) }
    var feedIsLive by remember { mutableStateOf(false) }
    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        location = repository.getCurrentLocation()
    }

    LaunchedEffect(Unit) {
        riskZones = SyntheticRiskData.zones()
        val feed = repository.getRiskZones()
        if (feed.isNotEmpty()) {
            riskZones = feed
            feedIsLive = feed.any { it.data_status == "live" }
        }
    }

    val topZones = remember(riskZones) {
        riskZones.sortedWith(
            compareByDescending<RiskZone> { riskLevelRank(it.risk_level) }
                .thenByDescending { it.risk_score }
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        AnimatedVisibility(
            visible = isEmergencyMode,
            enter = fadeIn(tween(250)) + slideInVertically(tween(300)) { -it / 3 }
        ) {
            ClaySurface(
                color = EmergencyRed,
                modifier = Modifier.fillMaxWidth(),
                shape = ClayShapes.tile,
                depth = 8.dp,
                contentColor = CanvasLight
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(Icons.Filled.Warning, null, tint = CanvasLight, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(T("home.evacMode"), color = CanvasLight, fontWeight = FontWeight.Black, fontSize = 14.sp)
                        Text(T("home.evacDesc"), color = CanvasLight.copy(alpha = 0.8f), fontSize = 11.sp)
                    }
                }
            }
        }
        // Render Auth Banner
        if (!repository.isLoggedIn()) {
            ClaySurface(
                color = ClayCreamTint,
                modifier = Modifier.fillMaxWidth(),
                shape = ClayShapes.tile,
                depth = 4.dp,
                tint = PrimaryGreen.copy(alpha = 0.35f)
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(RoundedCornerShape(10.dp))
                            .background(PrimaryGreen),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Filled.AccountCircle, null, tint = CanvasLight, modifier = Modifier.size(22.dp))
                    }
                    Spacer(Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            "Render Cloud Verification",
                            style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Bold),
                            color = TextPrimaryLight
                        )
                        Text(
                            "Sign in to sync alerts, reports & family check-ins with Render backend",
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                            color = TextSecondaryLight
                        )
                    }
                    Spacer(Modifier.width(8.dp))
                    Button(
                        onClick = onAuthClick,
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen),
                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text("SIGN IN", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = CanvasLight)
                    }
                }
            }
        } else {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                val isAdmin = repository.isAdmin()
                val roleName = if (isAdmin) "DISASTER ADMIN" else "CITIZEN"
                val roleColor = if (isAdmin) EmergencyRed else PrimaryGreen
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(androidx.compose.foundation.shape.CircleShape)
                            .background(roleColor)
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "${repository.getCurrentUserName() ?: repository.getCurrentUserPhone() ?: "User"}",
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 11.sp, fontWeight = FontWeight.Bold),
                        color = TextPrimaryLight
                    )
                    Spacer(Modifier.width(6.dp))
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = roleColor.copy(alpha = 0.12f)
                    ) {
                        Text(
                            roleName,
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Black),
                            color = roleColor,
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                        )
                    }
                }
                TextButton(
                    onClick = onAuthClick,
                    contentPadding = PaddingValues(0.dp)
                ) {
                    Text("Switch Role / Account", fontSize = 10.sp, color = TextSecondaryLight)
                }
            }
        }

        ClaySurface(
            color = MapBackground,
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp),
            shape = ClayShapes.cardLarge,
            depth = 10.dp,
            tint = BorderLight
        ) {
            Box(Modifier.fillMaxSize()) {
                CrisisMapView(
                    location = location,
                    riskZones = riskZones,
                    incidents = incidents,
                    isEmergencyMode = isEmergencyMode,
                    onMyLocationClick = {
                        scope.launch {
                            location = repository.getCurrentLocation()
                        }
                    },
                    onEmergencyToggle = { isEmergencyMode = !isEmergencyMode },
                    onRefreshIncidents = onRefreshIncidents,
                    isRefreshing = isRefreshingIncidents
                )
            }
        }

        EmergencySosButton(
            onClick = onTriggerSos,
            haptic = { haptic.performHapticFeedback(HapticFeedbackType.LongPress) }
        )

        // Live Incidents Section from Render / Swagger
        if (incidents.isNotEmpty()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(androidx.compose.foundation.shape.CircleShape)
                            .background(Color(0xFF10B981))
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "LIVE SWAGGER INCIDENTS (${incidents.size})",
                        style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Black),
                        color = TextPrimaryLight
                    )
                }
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = PrimaryGreen.copy(alpha = 0.12f)
                ) {
                    Text(
                        "Render Cloud Sync",
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Bold),
                        color = PrimaryGreen
                    )
                }
            }

            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                state = rememberLazyListState()
            ) {
                items(
                    items = incidents,
                    key = { it.id }
                ) { inc ->
                    IncidentFeedCard(inc)
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(T("home.riskZones"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight)
            DataSourceBadge(if (feedIsLive) "live" else "synthetic")
        }

        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            state = rememberLazyListState()
        ) {
            items(
                items = topZones.take(5),
                key = { it.zone_id ?: it.name ?: it.lat.toString() }
            ) { zone ->
                RiskZoneCard(zone)
            }
        }

        ClaySurface(
            color = ClayAmberTint,
            modifier = Modifier.fillMaxWidth(),
            shape = ClayShapes.tile,
            depth = 6.dp,
            tint = WarningAmber.copy(alpha = 0.4f)
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.Phone, null, tint = WarningAmber, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(T("home.smsFallback"), style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = TextPrimaryLight)
                    Text(T("home.smsDesc"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
                Surface(
                    shape = ClayShapes.chip,
                    color = WarningAmber.copy(alpha = 0.14f)
                ) {
                    Text(
                        T("home.featurePhones"),
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

@Composable
private fun RiskZoneCard(zone: RiskZone) {
    val levelColor = riskLevelColor(zone.risk_level)
    ClaySurface(
        color = ClayCreamTint,
        modifier = Modifier.width(200.dp),
        shape = ClayShapes.tile,
        depth = 6.dp,
        tint = levelColor.copy(alpha = 0.45f)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.LocationOn, null, tint = levelColor, modifier = Modifier.size(14.dp))
                SeverityBadge(zone.risk_level)
            }
            Spacer(Modifier.height(8.dp))
            Text(
                zone.name ?: T("home.riskZone"),
                style = MaterialTheme.typography.titleMedium.copy(fontSize = 13.sp),
                fontWeight = FontWeight.Black,
                maxLines = 2
            )
            Spacer(Modifier.height(6.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    riskScoreText(zone.risk_score),
                    style = MaterialTheme.typography.labelMedium.copy(fontSize = 10.sp),
                    color = levelColor,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.height(4.dp))
            Text(
                String.format("%.4f, %.4f", zone.lat, zone.lng),
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                color = TextSecondaryLight
            )
        }
    }
}

@Composable
private fun IncidentFeedCard(incident: IncidentOut) {
    val isVerified = incident.status.equals("verified", ignoreCase = true)
    val statusColor = if (isVerified) Color(0xFF10B981) else WarningAmber
    val sevColor = when (incident.severity) {
        5 -> EmergencyRed
        4 -> RiskHigh
        3 -> WarningAmber
        else -> RiskLow
    }

    ClaySurface(
        color = ClayCreamTint,
        modifier = Modifier.width(220.dp),
        shape = ClayShapes.tile,
        depth = 6.dp,
        tint = statusColor.copy(alpha = 0.35f)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = statusColor.copy(alpha = 0.15f)
                ) {
                    Text(
                        if (isVerified) "✓ VERIFIED" else "⚠ PENDING",
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Bold),
                        color = statusColor
                    )
                }
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = sevColor.copy(alpha = 0.15f)
                ) {
                    Text(
                        "SEV ${incident.severity}",
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Black),
                        color = sevColor
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Text(
                incident.type.replace('_', ' ').uppercase(),
                style = MaterialTheme.typography.titleMedium.copy(fontSize = 13.sp, fontWeight = FontWeight.Bold),
                maxLines = 1,
                color = TextPrimaryLight
            )
            if (!incident.description.isNullOrBlank()) {
                Spacer(Modifier.height(4.dp))
                Text(
                    incident.description,
                    style = MaterialTheme.typography.bodySmall.copy(fontSize = 10.sp),
                    color = TextSecondaryLight,
                    maxLines = 2,
                    overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis
                )
            }
            Spacer(Modifier.height(6.dp))
            Text(
                String.format("%.4f, %.4f", incident.lat, incident.lng),
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                color = TextSecondaryLight
            )
        }
    }
}

