package com.crisiscore.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.crisiscore.app.data.model.IncidentCategory
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun SosConfirmDialog(
    onConfirm: (String?) -> Unit,
    onDismiss: () -> Unit
) {
    var selectedCategory by remember { mutableStateOf<String?>(null) }

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(24.dp),
            color = CanvasLight,
            shadowElevation = 24.dp
        ) {
            Column(modifier = Modifier.padding(22.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Emergency, null, tint = EmergencyRed, modifier = Modifier.size(24.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(T.get("sos.confirmTitle"), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Black)
                    }
                    IconButton(onClick = onDismiss, modifier = Modifier.size(32.dp)) {
                        Icon(Icons.Filled.Close, null, tint = TextSecondaryLight, modifier = Modifier.size(20.dp))
                    }
                }

                Spacer(Modifier.height(12.dp))
                Text(T.get("sos.confirmWarning"), style = MaterialTheme.typography.bodyMedium, color = TextPrimaryLight)

                Spacer(Modifier.height(16.dp))
                Text(T.get("sos.selectCategoryOptional"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight, modifier = Modifier.padding(bottom = 8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(
                        "LANDSLIDE" to "⛰️",
                        "FLOOD" to "🌊",
                        "PERSON_TRAPPED" to "🏚️",
                        "OTHER" to "🚑"
                    ).forEach { (cat, emoji) ->
                        val isSelected = selectedCategory == cat
                        Surface(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(10.dp))
                                .clickable { selectedCategory = if (isSelected) null else cat },
                            shape = RoundedCornerShape(10.dp),
                            color = if (isSelected) EmergencyRed.copy(alpha = 0.15f) else SurfaceLight,
                            border = if (isSelected) BorderStroke(1.dp, SolidColor(EmergencyRed)) else ButtonDefaults.outlinedButtonBorder()
                        ) {
                            Column(
                                modifier = Modifier.padding(10.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(emoji, fontSize = 18.sp)
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    cat.replace("_", " "),
                                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Bold),
                                    color = if (isSelected) EmergencyRed else TextPrimaryLight,
                                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                                )
                            }
                        }
                    }
                }

                Spacer(Modifier.height(20.dp))
                CcButton(
                    onClick = { onConfirm(selectedCategory) },
                    variant = CcButtonVariant.Emergency,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Filled.Send, null, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(8.dp))
                    Text(T.get("sos.confirmButton"), fontWeight = FontWeight.Black, letterSpacing = 1.sp)
                }
                Spacer(Modifier.height(8.dp))
                CcButton(
                    onClick = onDismiss,
                    variant = CcButtonVariant.Ghost,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(T.get("sos.cancelButton"))
                }
            }
        }
    }
}
