package com.crisiscore.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
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
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.ui.theme.CanvasLight
import com.crisiscore.app.ui.theme.ClayCreamTint
import com.crisiscore.app.ui.theme.ClayRedTint
import com.crisiscore.app.ui.theme.ClayShapes
import com.crisiscore.app.ui.theme.EmergencyRed
import com.crisiscore.app.ui.theme.PrimaryGreen
import com.crisiscore.app.ui.theme.TextSecondaryLight
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
        shape = ClayShapes.card,
        color = CanvasLight.copy(alpha = 0.98f),
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .padding(horizontal = 14.dp, vertical = 10.dp)
                .statusBarsPadding(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .shadow(4.dp, ClayShapes.control, clip = false)
                        .clip(ClayShapes.control)
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
                    HeaderIconButton(
                        color = ClayCreamTint,
                        iconTint = PrimaryGreen,
                        onClick = { showLangMenu = true }
                    ) {
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

                HeaderIconButton(
                    color = ClayRedTint,
                    iconTint = EmergencyRed,
                    onClick = onHelpClick
                ) {
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

@Composable
private fun HeaderIconButton(
    color: Color,
    iconTint: Color,
    onClick: () -> Unit,
    content: @Composable () -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val scale by androidx.compose.animation.core.animateFloatAsState(
        targetValue = if (isPressed) 0.88f else 1f,
        animationSpec = androidx.compose.animation.core.tween(80),
        label = "headerBtn"
    )

    Box(
        modifier = Modifier
            .size(40.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            }
            .shadow(3.dp, ClayShapes.control, clip = false)
            .clip(ClayShapes.control)
            .background(color)
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                onClick = onClick
            ),
        contentAlignment = Alignment.Center
    ) {
        content()
    }
}
