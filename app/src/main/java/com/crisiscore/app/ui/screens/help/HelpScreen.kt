package com.crisiscore.app.ui.screens.help

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.Helpline
import com.crisiscore.app.data.model.HelplineColorType
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.LocaleManager
import com.crisiscore.app.util.T
import com.crisiscore.app.util.TtsManager

@Composable
fun HelpScreen() {
    val context = LocalContext.current
    val helplines = listOf(
        Helpline(T("help.ndrfTitle"), "1078", "+91 11 26701728", T("help.ndrfDesc"), T("help.ndrfBadge"), HelplineColorType.RED),
        Helpline(T("help.seocTitle"), "1070", "+91 361 2237221", T("help.seocDesc"), T("help.seocBadge"), HelplineColorType.GREEN),
        Helpline(T("help.medicalTitle"), "108", "102", T("help.medicalDesc"), T("help.medicalBadge"), HelplineColorType.RED),
        Helpline(T("help.policeTitle"), "112", "100", T("help.policeDesc"), T("help.policeBadge"), HelplineColorType.GREEN),
        Helpline(T("help.fireTitle"), "101", "+91 361 2540101", T("help.fireDesc"), T("help.fireBadge"), HelplineColorType.AMBER),
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 14.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T("help.categoryHeader"), title = T("help.title"))

        // Audio readout banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = SurfaceLight,
            border = ButtonDefaults.outlinedButtonBorder()
        ) {
            Row(
                modifier = Modifier.padding(14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(PrimaryGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Filled.Headset, null, tint = CanvasLight, modifier = Modifier.size(24.dp))
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(T("help.subtitle"), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text(T("help.tollFreeSub"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
                IconButton(onClick = {
                    val speech = helplines.joinToString(". ") { "${it.title}: dial ${it.number}" }
                    TtsManager.speak(speech, LocaleManager.currentLanguage.value)
                }) {
                    Icon(Icons.Filled.VolumeUp, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp))
                }
            }
        }

        // Helplines
        Text(T("help.helplinesHeader"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)

        helplines.forEach { helpline ->
            HelplineCard(helpline) {
                val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:${helpline.number}"))
                context.startActivity(intent)
            }
        }

        // Official Directory
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = MapBackground
        ) {
            Text(T("help.agenciesHeader"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)
            Spacer(Modifier.height(10.dp))

            val agencies = listOf(
                Triple(T("help.ndrfHq"), T("help.ndrfLoc"), "+91 361 2840001"),
                Triple(T("help.sdrfHq"), T("help.sdrfLoc"), "+91 361 2237011"),
                Triple(T("help.mdonerHq"), T("help.mdonerLoc"), "+91 364 2522000"),
            )

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                agencies.forEach { (name, loc, phone) ->
                    Surface(
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        color = SurfaceLight
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text(name, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), fontWeight = FontWeight.Bold, color = TextPrimaryLight)
                            Text(loc, style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
                            Text(phone, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp, fontWeight = FontWeight.Bold, color = PrimaryGreen), modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            }
        }

        // Survival Guidance
        Text(T("help.guidanceHeader"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            GuidanceCard(T("help.landslideTitle"), EmergencyRed, T("help.landslideGuidance"), Modifier.weight(1f))
            GuidanceCard(T("help.floodTitle"), PrimaryGreen, T("help.floodGuidance"), Modifier.weight(1f))
            GuidanceCard(T("help.quakeTitle"), WarningAmber, T("help.quakeGuidance"), Modifier.weight(1f))
        }

        // Offline SMS notice
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            borderColor = EmergencyRed.copy(alpha = 0.4f),
            backgroundColor = EmergencyRed.copy(alpha = 0.05f)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Sms, null, tint = EmergencyRed, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(T("help.offlineTitle"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 11.sp), color = EmergencyRed, fontWeight = FontWeight.Black)
                    Spacer(Modifier.height(4.dp))
                    Text(T("help.offlineMessage"), style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), color = TextPrimaryLight)
                }
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun HelplineCard(helpline: Helpline, onCall: () -> Unit) {
    val color = when (helpline.colorType) {
        HelplineColorType.RED -> EmergencyRed
        HelplineColorType.GREEN -> PrimaryGreen
        HelplineColorType.AMBER -> WarningAmber
    }

    CcCard(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(color.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    when (helpline.colorType) {
                        HelplineColorType.RED -> Icons.Filled.Warning
                        HelplineColorType.GREEN -> Icons.Filled.Headset
                        HelplineColorType.AMBER -> Icons.Filled.LocalFireDepartment
                    },
                    null, tint = color, modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(helpline.title, style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                    Spacer(Modifier.width(6.dp))
                    Surface(shape = RoundedCornerShape(4.dp), color = TextPrimaryLight.copy(alpha = 0.1f)) {
                        Text(helpline.badge, modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp), style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp), color = TextPrimaryLight)
                    }
                }
                Text(helpline.description, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), color = TextSecondaryLight, modifier = Modifier.padding(top = 2.dp))
            }
            CcButton(onClick = onCall, variant = CcButtonVariant.Emergency) {
                Icon(Icons.Filled.Phone, null, modifier = Modifier.size(14.dp))
                Spacer(Modifier.width(4.dp))
                Text("${T("help.callButton")} (${helpline.number})", style = MaterialTheme.typography.bodySmall.copy(fontSize = 10.sp))
            }
        }
    }
}

@Composable
private fun GuidanceCard(title: String, color: androidx.compose.ui.graphics.Color, text: String, modifier: Modifier = Modifier) {
    CcCard(modifier = modifier, borderColor = color.copy(alpha = 0.3f)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                when (color) {
                    EmergencyRed -> Icons.Filled.Warning
                    PrimaryGreen -> Icons.Filled.Water
                    else -> Icons.Filled.Landscape
                },
                null, tint = color, modifier = Modifier.size(14.dp)
            )
            Spacer(Modifier.width(6.dp))
            Text(title, style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = color, fontWeight = FontWeight.Black)
        }
        Spacer(Modifier.height(6.dp))
        Text(text, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), color = TextPrimaryLight)
    }
}
