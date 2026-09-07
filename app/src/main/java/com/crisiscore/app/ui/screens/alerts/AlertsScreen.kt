package com.crisiscore.app.ui.screens.alerts

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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.Alert
import com.crisiscore.app.data.model.SeverityLevel
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun AlertsScreen() {
    val alerts = listOf(
        Alert(
            id = "alert-1",
            title = T("alerts.sample1.title"),
            body = T("alerts.sample1.body"),
            level = SeverityLevel.CRITICAL,
            issuedAgo = T("alerts.sample1.issuedAgo"),
            source = T("alerts.sample1.source")
        ),
        Alert(
            id = "alert-2",
            title = T("alerts.sample2.title"),
            body = T("alerts.sample2.body"),
            level = SeverityLevel.HIGH,
            issuedAgo = T("alerts.sample2.issuedAgo"),
            source = T("alerts.sample2.source")
        )
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 14.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T("alerts.headerTag"), title = T("alerts.title"))

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
                Text(T("alerts.sub"), style = MaterialTheme.typography.bodySmall, color = TextPrimaryLight)
            }
        }

        // Alert cards
        alerts.forEach { alert ->
            AlertCard(alert)
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun AlertCard(alert: Alert) {
    val borderColor = when (alert.level) {
        SeverityLevel.CRITICAL -> EmergencyRed
        SeverityLevel.HIGH -> WarningAmber
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
                Text(alert.title, style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp), color = borderColor, fontWeight = FontWeight.Bold)
            }
            SeverityBadge(alert.level.name)
        }

        Spacer(Modifier.height(10.dp))

        Text(alert.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(4.dp))
        Text(alert.body, style = MaterialTheme.typography.bodySmall, color = TextPrimaryLight)

        Spacer(Modifier.height(10.dp))
        HorizontalDivider(color = BorderLight)
        Spacer(Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                T("alerts.issuedInfo").replace("{time}", alert.issuedAgo).replace("{source}", alert.source),
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                color = TextSecondaryLight
            )
            IconButton(onClick = { /* Audio readout */ }, modifier = Modifier.size(28.dp)) {
                Icon(Icons.Filled.VolumeUp, null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
            }
        }
    }
}
