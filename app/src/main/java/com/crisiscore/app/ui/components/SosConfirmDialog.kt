package com.crisiscore.app.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun SosConfirmDialog(
    onConfirm: (String?) -> Unit,
    onDismiss: () -> Unit
) {
    var selectedCategory by remember { mutableStateOf<String?>(null) }

    Dialog(onDismissRequest = onDismiss) {
        ClaySurface(
            color = CanvasLight,
            modifier = Modifier.fillMaxWidth(),
            shape = ClayShapes.cardLarge,
            depth = 16.dp,
            tint = EmergencyRed.copy(alpha = 0.5f)
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Box(modifier = Modifier.fillMaxWidth()) {
                    Icon(
                        Icons.Filled.Emergency, null,
                        tint = EmergencyRed,
                        modifier = Modifier
                            .size(28.dp)
                            .align(Alignment.TopCenter)
                    )
                    ClaySurface(
                        color = ClayRedTint,
                        modifier = Modifier
                            .size(28.dp)
                            .align(Alignment.TopEnd),
                        shape = ClayShapes.chip,
                        depth = 2.dp,
                        contentColor = TextSecondaryLight,
                        onClick = onDismiss
                    ) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Icon(Icons.Filled.Close, null, tint = TextSecondaryLight, modifier = Modifier.size(16.dp))
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))
                Text(
                    T("sos.confirmTitle"),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Black,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )

                Spacer(Modifier.height(8.dp))
                Text(
                    T("sos.confirmWarning"),
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextPrimaryLight,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )

                Spacer(Modifier.height(16.dp))
                Text(
                    T("sos.selectCategoryOptional"),
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondaryLight,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )

                Spacer(Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    listOf(
                        "LANDSLIDE" to "⛰\uFE0F",
                        "FLOOD" to "\uD83C\uDF0A",
                        "PERSON_TRAPPED" to "\uD83C\uDFDA\uFE0F",
                        "OTHER" to "\uD83C\uDE91"
                    ).forEach { (cat, emoji) ->
                        val isSelected = selectedCategory == cat
                        SosCategoryTile(
                            category = cat,
                            emoji = emoji,
                            isSelected = isSelected,
                            modifier = Modifier.weight(1f),
                            onClick = { selectedCategory = if (isSelected) null else cat }
                        )
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
                    Text(T("sos.confirmButton"), fontWeight = FontWeight.Black, letterSpacing = 1.sp)
                }

                Spacer(Modifier.height(8.dp))
                CcButton(
                    onClick = onDismiss,
                    variant = CcButtonVariant.Ghost,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(T("sos.cancelButton"), color = TextSecondaryLight)
                }
            }
        }
    }
}

@Composable
private fun SosCategoryTile(
    category: String,
    emoji: String,
    isSelected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    ClaySurface(
        color = if (isSelected) EmergencyRed.copy(alpha = 0.16f) else ClayCreamTint,
        modifier = modifier,
        shape = ClayShapes.control,
        depth = if (isSelected) 4.dp else 2.dp,
        tint = if (isSelected) EmergencyRed else BorderLight,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp, horizontal = 4.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(emoji, fontSize = 22.sp)
            Spacer(Modifier.height(6.dp))
            Text(
                T("cat.${category}"),
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Bold, lineHeight = 12.sp),
                color = if (isSelected) EmergencyRed else TextPrimaryLight,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}