package com.crisiscore.app.ui.screens.status

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.SosState
import com.crisiscore.app.data.model.SosStatusDetail
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun StatusScreen(
    sosState: SosState,
    sosDetail: SosStatusDetail,
    onReset: () -> Unit,
    onSimulate: (SosState) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T("status.headerTag"), title = T("status.headerTitle"))

        if (sosState != SosState.IDLE) {
            ActiveSosTracker(sosState, sosDetail, onReset)
        } else {
            EmptySosState()
        }

        // Volunteer Verification QR
        CcCard(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(PrimaryGreen.copy(alpha = 0.1f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Filled.Shield, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(T("status.verifyTitle"), style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                    Text(T("status.verifySubtitle"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
                CcButton(onClick = {}, variant = CcButtonVariant.Secondary) {
                    Icon(Icons.Filled.QrCodeScanner, null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(4.dp))
                    Text(T("status.verifyButton"), style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        // State Simulator
        CcCard(modifier = Modifier.fillMaxWidth()) {
            Text(T("status.simulatorTitle"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)
            Spacer(Modifier.height(4.dp))
            Text(
                T("status.simulatorText"),
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondaryLight
            )
            Spacer(Modifier.height(10.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                listOf(
                    SosState.IDLE, SosState.SENDING, SosState.SENT,
                    SosState.VERIFIED, SosState.VOLUNTEER_EN_ROUTE, SosState.RESOLVED
                ).forEach { state ->
                    val isActive = sosState == state
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(8.dp))
                            .clickable { onSimulate(state) },
                        shape = RoundedCornerShape(8.dp),
                        color = if (isActive) PrimaryGreen else SurfaceLight,
                        border = if (isActive) null else ButtonDefaults.outlinedButtonBorder()
                    ) {
                        Text(
                            state.name.take(6),
                            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                            color = if (isActive) CanvasLight else TextPrimaryLight,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun ActiveSosTracker(
    sosState: SosState,
    sosDetail: SosStatusDetail,
    onReset: () -> Unit
) {
    val steps = listOf(
        Triple(T("status.stepSending"), T("status.descSending"), Icons.Filled.Send),
        Triple(T("status.stepReceived"), T("status.descReceived"), Icons.Filled.Inbox),
        Triple(T("status.stepVerified"), T("status.descVerified"), Icons.Filled.Verified),
        Triple(T("status.stepEnRoute"), T("status.descEnRoute"), Icons.Filled.DirectionsRun),
        Triple(T("status.stepResolved"), T("status.descResolved"), Icons.Filled.CheckCircle),
    )

    val currentIndex = when (sosState) {
        SosState.SENDING -> 0
        SosState.SENT -> 1
        SosState.OFFLINE_QUEUED -> 1
        SosState.VERIFIED -> 2
        SosState.ASSIGNED, SosState.VOLUNTEER_EN_ROUTE -> 3
        SosState.HELP_ARRIVED, SosState.RESOLVED -> 4
        SosState.ERROR -> -1
        else -> -1
    }

    CcCard(
        modifier = Modifier.fillMaxWidth(),
        borderColor = if (sosState == SosState.ERROR) EmergencyRed else PrimaryGreen
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                "${T("status.sosTracker")} \u2022 ${sosDetail.sosId ?: T("status.pending")}",
                style = MaterialTheme.typography.labelSmall.copy(letterSpacing = 1.sp),
                color = TextSecondaryLight
            )
            DataSourceBadge()
        }

        Spacer(Modifier.height(16.dp))

        // Timeline stepper
        steps.forEachIndexed { index, (title, desc, icon) ->
            val isCompleted = index <= currentIndex
            val isCurrent = index == currentIndex
            val isError = currentIndex == -1 && index == 0
            val lineColor by animateColorAsState(
                if (isCompleted) PrimaryGreen else BorderLight,
                label = "lineColor$index"
            )
            val iconBg by animateColorAsState(
                when {
                    isError -> EmergencyRed
                    isCompleted -> PrimaryGreen
                    else -> SurfaceLight
                },
                label = "iconBg$index"
            )
            val iconTint by animateColorAsState(
                if (isCompleted) CanvasLight else TextSecondaryLight,
                label = "iconTint$index"
            )

            Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.width(40.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(32.dp)
                            .clip(CircleShape)
                            .background(iconBg),
                        contentAlignment = Alignment.Center
                    ) {
                        if (isCurrent && sosState == SosState.SENDING) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                color = CanvasLight,
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(icon, null, tint = iconTint, modifier = Modifier.size(16.dp))
                        }
                    }
                    if (index < steps.lastIndex) {
                        Box(
                            modifier = Modifier
                                .width(2.dp)
                                .height(28.dp)
                                .background(lineColor)
                        )
                    }
                }
                Spacer(Modifier.width(8.dp))
                Column(modifier = Modifier.padding(top = 4.dp)) {
                    Text(
                        title,
                        style = MaterialTheme.typography.bodySmall.copy(
                            fontWeight = if (isCurrent) FontWeight.Black else FontWeight.Normal,
                            fontSize = 12.sp
                        ),
                        color = if (isCompleted) TextPrimaryLight else TextSecondaryLight
                    )
                    Text(desc, style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp), color = TextSecondaryLight)
                    if (index == currentIndex) {
                        Spacer(Modifier.height(4.dp))
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = PrimaryGreen.copy(alpha = 0.08f)
                        ) {
                            Text(
                                T("status.currentStep"),
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                                color = PrimaryGreen,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
            if (index < steps.lastIndex) Spacer(Modifier.height(0.dp))
        }

        // Responder info
        if (sosDetail.assignedVolunteerName != null) {
            Spacer(Modifier.height(12.dp))
            HorizontalDivider(color = BorderLight)
            Spacer(Modifier.height(12.dp))
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                color = SurfaceLight
            ) {
                Row(
                    modifier = Modifier.padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(Icons.Filled.Person, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp))
                    Spacer(Modifier.width(10.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(sosDetail.assignedVolunteerName, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = PrimaryGreen)
                        if (sosDetail.etaMinutes != null) {
                            Text("${T("status.eta")} ${sosDetail.etaMinutes} ${T("status.mins")}", style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                        }
                    }
                    CcButton(onClick = {}, variant = CcButtonVariant.Secondary) {
                        Icon(Icons.Filled.Phone, null, modifier = Modifier.size(14.dp))
                        Spacer(Modifier.width(4.dp))
                        Text(T("status.call"), style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }

        Spacer(Modifier.height(12.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("${T("status.stateLabel")} ${sosState.name}", style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight)
            CcButton(onClick = onReset, variant = CcButtonVariant.Outline) {
                Text(T("status.resetButton"))
            }
        }
    }
}

@Composable
private fun EmptySosState() {
    CcCard(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(SurfaceLight),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    Icons.Filled.History,
                    null,
                    tint = TextSecondaryLight.copy(alpha = 0.5f),
                    modifier = Modifier.size(32.dp)
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(T("status.noSignalTitle"), style = MaterialTheme.typography.titleMedium, color = TextPrimaryLight)
            Text(
                T("status.noSignalText"),
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondaryLight,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(horizontal = 32.dp).padding(top = 4.dp)
            )
        }
    }
}
