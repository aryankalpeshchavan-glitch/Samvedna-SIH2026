package com.crisiscore.app.ui.screens.home

import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
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
    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        location = repository.getCurrentLocation()
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
                        location = repository.getCurrentLocation()
                    }
                },
                onEmergencyToggle = { isEmergencyMode = !isEmergencyMode }
            )
        }

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .then(
                    Modifier.graphicsLayer {
                        scaleX = pulseScale
                        scaleY = pulseScale
                        alpha = pulseAlpha
                    }
                ),
            shape = RoundedCornerShape(16.dp),
            color = EmergencyRed,
            onClick = {
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                onTriggerSos()
            }
        ) {
            Row(
                modifier = Modifier.padding(vertical = 18.dp, horizontal = 20.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.Emergency, null, tint = CanvasLight, modifier = Modifier.size(28.dp))
                Spacer(Modifier.width(14.dp))
                Column {
                    Text(
                        T.get("home.triggerSos"),
                        color = CanvasLight,
                        fontWeight = FontWeight.Black,
                        fontSize = 16.sp,
                        letterSpacing = 1.5.sp
                    )
                    Text(
                        T.get("home.sosDescription"),
                        color = CanvasLight.copy(alpha = 0.75f),
                        fontSize = 11.sp,
                        letterSpacing = 0.8.sp
                    )
                }
            }
        }

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
