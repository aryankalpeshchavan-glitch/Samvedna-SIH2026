package com.crisiscore.app.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

enum class TabType { Home, Incident, Status, Family, Alerts, Help }

@Composable
fun BottomNavBar(
    activeTab: TabType,
    onTabChange: (TabType) -> Unit,
    sosActive: Boolean,
    modifier: Modifier = Modifier
) {
    data class TabItem(val id: TabType, val labelKey: String, val icon: ImageVector, val activeIcon: ImageVector)

    val tabs = listOf(
        TabItem(TabType.Home, "nav.map", Icons.Outlined.Map, Icons.Filled.Map),
        TabItem(TabType.Incident, "nav.report", Icons.Outlined.Warning, Icons.Filled.Warning),
        TabItem(TabType.Status, "nav.sosStatus", Icons.Outlined.LocationOn, Icons.Filled.LocationOn),
        TabItem(TabType.Family, "nav.family", Icons.Outlined.People, Icons.Filled.People),
        TabItem(TabType.Alerts, "nav.alerts", Icons.Outlined.Notifications, Icons.Filled.Notifications),
        TabItem(TabType.Help, "nav.help", Icons.Outlined.Help, Icons.Filled.Help),
    )

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        color = CanvasLight.copy(alpha = 0.95f),
        shadowElevation = 8.dp,
        tonalElevation = 0.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 4.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            tabs.forEach { tab ->
                val isActive = activeTab == tab.id
                val isSosIndicator = tab.id == TabType.Status && sosActive

                val bgColor by animateColorAsState(
                    if (isActive) PrimaryGreen else MaterialTheme.colorScheme.surface,
                    label = "tabBg"
                )
                val contentColor by animateColorAsState(
                    if (isActive) CanvasLight else TextSecondaryLight,
                    label = "tabContent"
                )
                val size by animateDpAsState(
                    if (isActive) 48.dp else 40.dp,
                    label = "tabSize"
                )
                val iconScale by animateFloatAsState(
                    if (isActive) 1.1f else 1f,
                    label = "iconScale"
                )

                Column(
                    modifier = Modifier
                        .clip(RoundedCornerShape(14.dp))
                        .clickable(
                            interactionSource = remember { MutableInteractionSource() },
                            indication = null
                        ) { onTabChange(tab.id) }
                        .padding(horizontal = 4.dp, vertical = 4.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        modifier = Modifier
                            .size(size)
                            .clip(RoundedCornerShape(14.dp))
                            .background(bgColor),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = if (isActive) tab.activeIcon else tab.icon,
                            contentDescription = T.get(tab.labelKey),
                            tint = contentColor,
                            modifier = Modifier.size(if (isActive) 24.dp else 20.dp)
                        )
                        if (isSosIndicator) {
                            Box(
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .padding(2.dp)
                                    .size(10.dp)
                                    .clip(CircleShape)
                                    .background(EmergencyRed)
                            )
                        }
                    }
                    Spacer(Modifier.height(2.dp))
                    Text(
                        T.get(tab.labelKey),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 9.sp,
                            letterSpacing = 0.sp
                        ),
                        color = if (isActive) PrimaryGreen else TextSecondaryLight,
                        textAlign = TextAlign.Center,
                        maxLines = 1
                    )
                }
            }
        }
    }
}
