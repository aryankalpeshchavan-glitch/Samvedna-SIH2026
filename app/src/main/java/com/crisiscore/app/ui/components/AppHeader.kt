package com.crisiscore.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.LocaleManager
import com.crisiscore.app.util.T

@Composable
fun AppHeader(
    modifier: Modifier = Modifier,
    onHelpClick: () -> Unit = {}
) {
    val currentLang by LocaleManager.currentLanguage.collectAsState()
    var showLangMenu by remember { mutableStateOf(false) }

    Surface(
        modifier = modifier.fillMaxWidth(),
        color = CanvasLight.copy(alpha = 0.95f),
        shadowElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .padding(horizontal = 16.dp, vertical = 10.dp)
                .statusBarsPadding(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(RoundedCornerShape(10.dp))
                        .background(PrimaryGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        Icons.Filled.Shield,
                        contentDescription = null,
                        tint = CanvasLight,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(
                        "SAMVEDNA",
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontSize = 17.sp,
                            letterSpacing = 2.sp,
                            fontWeight = FontWeight.Black
                        )
                    )
                    Text(
                        T.get("nav.subtitle"),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 8.sp,
                            letterSpacing = 0.5.sp,
                            color = TextSecondaryLight
                        )
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Box {
                    IconButton(onClick = { showLangMenu = true }) {
                        Icon(
                            Icons.Outlined.Language,
                            contentDescription = "Language",
                            tint = PrimaryGreen,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                    DropdownMenu(expanded = showLangMenu, onDismissRequest = { showLangMenu = false }) {
                        LocaleManager.supportedLanguages.forEach { (code, label, native) ->
                            DropdownMenuItem(
                                text = {
                                    Row {
                                        Text(native, fontWeight = if (currentLang == code) FontWeight.Bold else FontWeight.Normal)
                                        Spacer(Modifier.width(8.dp))
                                        Text(label, color = TextSecondaryLight, fontSize = 11.sp)
                                    }
                                },
                                onClick = {
                                    LocaleManager.setLanguage(code)
                                    showLangMenu = false
                                }
                            )
                        }
                    }
                }

                IconButton(onClick = onHelpClick) {
                    Icon(
                        Icons.Outlined.HelpOutline,
                        contentDescription = T.get("nav.help"),
                        tint = EmergencyRed,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}
