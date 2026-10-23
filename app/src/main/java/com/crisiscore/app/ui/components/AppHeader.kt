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
    onHelpClick: () -> Unit = {},
    onAuthClick: () -> Unit = {},
    isLoggedIn: Boolean = false,
    userNameOrPhone: String? = null,
    userRole: String? = null,
    onLogout: () -> Unit = {}
) {
    val currentLang by LocaleManager.currentLanguage.collectAsState()
    var showLangMenu by remember { mutableStateOf(false) }
    var showUserMenu by remember { mutableStateOf(false) }

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = ClayShapes.card,
        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.98f),
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
                // Language selector
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

                // Role Badge pill if logged in
                if (isLoggedIn) {
                    val isAdmin = userRole?.lowercase() == "admin" || userRole?.lowercase() == "officer"
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = if (isAdmin) EmergencyRed.copy(alpha = 0.12f) else PrimaryGreen.copy(alpha = 0.12f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, if (isAdmin) EmergencyRed.copy(alpha = 0.4f) else PrimaryGreen.copy(alpha = 0.4f))
                    ) {
                        Text(
                            text = if (isAdmin) "ADMIN" else "CITIZEN",
                            style = MaterialTheme.typography.labelSmall.copy(
                                fontSize = 8.sp,
                                fontWeight = FontWeight.Black,
                                letterSpacing = 0.5.sp
                            ),
                            color = if (isAdmin) EmergencyRed else PrimaryGreen,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                // Auth / Profile Button
                Box {
                    HeaderIconButton(
                        color = if (isLoggedIn) PrimaryGreen.copy(alpha = 0.12f) else ClayCreamTint,
                        iconTint = if (isLoggedIn) PrimaryGreen else TextSecondaryLight,
                        onClick = {
                            if (isLoggedIn) {
                                showUserMenu = true
                            } else {
                                onAuthClick()
                            }
                        }
                    ) {
                        Box(contentAlignment = Alignment.TopEnd) {
                            Icon(
                                if (isLoggedIn) Icons.Outlined.Person else Icons.Outlined.Login,
                                contentDescription = if (isLoggedIn) "Account" else "Sign In",
                                tint = if (isLoggedIn) PrimaryGreen else TextSecondaryLight,
                                modifier = Modifier.size(20.dp)
                            )
                            if (isLoggedIn) {
                                Box(
                                    modifier = Modifier
                                        .size(6.dp)
                                        .clip(androidx.compose.foundation.shape.CircleShape)
                                        .background(PrimaryGreen)
                                )
                            }
                        }
                    }

                    if (isLoggedIn) {
                        DropdownMenu(
                            expanded = showUserMenu,
                            onDismissRequest = { showUserMenu = false }
                        ) {
                            DropdownMenuItem(
                                text = {
                                    Column {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Text(
                                                userNameOrPhone ?: "Citizen",
                                                fontWeight = FontWeight.Bold,
                                                style = MaterialTheme.typography.bodyMedium
                                            )
                                            Spacer(Modifier.width(6.dp))
                                            val isAdmin = userRole?.lowercase() == "admin" || userRole?.lowercase() == "officer"
                                            Surface(
                                                shape = RoundedCornerShape(4.dp),
                                                color = if (isAdmin) EmergencyRed.copy(alpha = 0.15f) else PrimaryGreen.copy(alpha = 0.15f)
                                            ) {
                                                Text(
                                                    if (isAdmin) "ADMIN" else "CITIZEN",
                                                    fontSize = 8.sp,
                                                    fontWeight = FontWeight.Black,
                                                    color = if (isAdmin) EmergencyRed else PrimaryGreen,
                                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                                )
                                            }
                                        }
                                        Text(
                                            if (userRole?.lowercase() == "admin") "Command Center Clearance" else "Citizen Community Access",
                                            color = if (userRole?.lowercase() == "admin") EmergencyRed else PrimaryGreen,
                                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp)
                                        )
                                    }
                                },
                                onClick = { /* noop */ },
                                enabled = false
                            )
                            HorizontalDivider()
                            DropdownMenuItem(
                                text = {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(
                                            Icons.Outlined.Logout,
                                            contentDescription = null,
                                            tint = EmergencyRed,
                                            modifier = Modifier.size(18.dp)
                                        )
                                        Spacer(Modifier.width(8.dp))
                                        Text("Sign Out", color = EmergencyRed)
                                    }
                                },
                                onClick = {
                                    showUserMenu = false
                                    onLogout()
                                }
                            )
                        }
                    }
                }

                // Help Button
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
