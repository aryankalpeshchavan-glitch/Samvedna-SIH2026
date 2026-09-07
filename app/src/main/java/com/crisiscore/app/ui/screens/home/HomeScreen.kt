package com.crisiscore.app.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.local.SyntheticRiskData
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
        if (isEmergencyMode) {
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
                    isEmergencyMode = isEmergencyMode,
                    onMyLocationClick = {
                        scope.launch {
                            location = repository.getCurrentLocation()
                        }
                    },
                    onEmergencyToggle = { isEmergencyMode = !isEmergencyMode }
                )
            }
        }

        EmergencySosButton(
            onClick = onTriggerSos,
            haptic = { haptic.performHapticFeedback(HapticFeedbackType.LongPress) }
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(T("home.riskZones"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight)
            DataSourceBadge(if (feedIsLive) "live" else "synthetic")
        }

        LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            items(topZones.take(5), key = { it.zone_id ?: it.name ?: it.lat.toString() }) { zone ->
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