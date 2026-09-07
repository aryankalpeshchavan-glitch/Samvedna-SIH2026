package com.crisiscore.app.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
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

    ClaySurface(
        color = CanvasLight.copy(alpha = 0.97f),
        modifier = modifier.fillMaxWidth(),
        shape = ClayShapes.card,
        depth = 8.dp
    ) {
        Row(
            modifier = Modifier
                .padding(horizontal = 14.dp, vertical = 10.dp)
                .statusBarsPadding(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                ClaySurface(
                    color = PrimaryGreen,
                    modifier = Modifier.size(38.dp),
                    shape = ClayShapes.control,
                    depth = 6.dp,
                    contentColor = CanvasLight
                ) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Icon(
                            Icons.Filled.Shield,
                            contentDescription = null,
                            tint = CanvasLight,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(
                        T("app.name"),
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontSize = 17.sp,
                            letterSpacing = 2.sp,
                            fontWeight = FontWeight.Black
                        )
                    )
                    Text(
                        T("nav.subtitle"),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 8.sp,
                            letterSpacing = 0.5.sp,
                            color = TextSecondaryLight
                        )
                    )
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Box {
                    ClaySurface(
                        color = ClayCreamTint,
                        modifier = Modifier.size(40.dp),
                        shape = ClayShapes.control,
                        depth = 4.dp,
                        contentColor = PrimaryGreen,
                        onClick = { showLangMenu = true }
                    ) {
                        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            Icon(
                                Icons.Outlined.Language,
                                contentDescription = "Language",
                                tint = PrimaryGreen,
                                modifier = Modifier.size(20.dp)
                            )
                        }
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

                ClaySurface(
                    color = ClayRedTint,
                    modifier = Modifier.size(40.dp),
                    shape = ClayShapes.control,
                    depth = 4.dp,
                    contentColor = EmergencyRed,
                    onClick = onHelpClick
                ) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Icon(
                            Icons.Outlined.HelpOutline,
                            contentDescription = T("nav.help"),
                            tint = EmergencyRed,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }
            }
        }
    }
}