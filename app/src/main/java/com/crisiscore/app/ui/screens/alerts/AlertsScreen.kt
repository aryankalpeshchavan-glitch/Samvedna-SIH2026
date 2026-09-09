package com.crisiscore.app.ui.screens.alerts

import androidx.compose.foundation.background
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.NotificationLogOut
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun AlertsScreen(repository: CrisisCoreRepository) {
    var notifications by remember { mutableStateOf<List<NotificationLogOut>>(emptyList()) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        notifications = repository.getNotifications()
        isLoading = false
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 14.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T.get("alerts.headerTag"), title = T.get("alerts.title"))

        // Info banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            color = SurfaceLight
        ) {
            Row(
                modifier = Modifier.padding(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.Shield, null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(T.get("alerts.sub"), style = MaterialTheme.typography.bodySmall, color = TextPrimaryLight)
            }
        }

        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = PrimaryGreen, strokeWidth = 2.dp)
            }
        } else if (notifications.isEmpty()) {
            CcCard(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 28.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(
                        modifier = Modifier
                            .size(56.dp)
                            .clip(CircleShape)
                            .background(PrimaryGreen.copy(alpha = 0.1f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            Icons.Filled.CheckCircle,
                            null,
                            tint = PrimaryGreen,
                            modifier = Modifier.size(32.dp)
                        )
                    }
                    Spacer(Modifier.height(12.dp))
                    Text("ALL CLEAR IN YOUR SECTOR", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = TextPrimaryLight)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "No active disaster notifications, flash flood advisories, or evacuation orders have been broadcast for your area.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondaryLight,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 24.dp)
                    )
                }
            }
        } else {
            notifications.forEach { item ->
                NotificationCard(item)
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun NotificationCard(notification: NotificationLogOut) {
    val borderColor = when (notification.priority.uppercase()) {
        "HIGH", "URGENT", "CRITICAL" -> EmergencyRed
        "MEDIUM", "WARNING" -> WarningAmber
        else -> PrimaryGreen
    }

    CcCard(
        modifier = Modifier.fillMaxWidth(),
        borderColor = borderColor
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Warning, null, tint = borderColor, modifier = Modifier.size(14.dp))
                Spacer(Modifier.width(6.dp))
                Text(
                    "ALERT #${notification.id} \u2022 ${notification.channel.uppercase()}",
                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                    color = borderColor,
                    fontWeight = FontWeight.Bold
                )
            }
            DataSourceBadge(notification.data_label)
        }

        Spacer(Modifier.height(10.dp))

        Text(notification.message, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold, color = TextPrimaryLight)

        Spacer(Modifier.height(10.dp))
        HorizontalDivider(color = BorderLight)
        Spacer(Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "Status: ${notification.status} \u2022 Sent: ${notification.sent_at ?: "Recent"}",
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                color = TextSecondaryLight
            )
            IconButton(onClick = { /* Audio readout */ }, modifier = Modifier.size(28.dp)) {
                Icon(Icons.Filled.VolumeUp, null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
            }
        }
    }
}
