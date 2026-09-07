package com.crisiscore.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

enum class TabType { Home, Incident, Status, Family, Alerts, Help }

private data class NavTabItem(val id: TabType, val labelKey: String, val icon: ImageVector, val activeIcon: ImageVector)

@Composable
fun BottomNavBar(
    activeTab: TabType,
    onTabChange: (TabType) -> Unit,
    sosActive: Boolean,
    modifier: Modifier = Modifier
) {
    val tabs = listOf(
        NavTabItem(TabType.Home, "nav.map", Icons.Outlined.Map, Icons.Filled.Map),
        NavTabItem(TabType.Incident, "nav.report", Icons.Outlined.Warning, Icons.Filled.Warning),
        NavTabItem(TabType.Status, "nav.sosStatus", Icons.Outlined.LocationOn, Icons.Filled.LocationOn),
        NavTabItem(TabType.Family, "nav.family", Icons.Outlined.People, Icons.Filled.People),
        NavTabItem(TabType.Alerts, "nav.alerts", Icons.Outlined.Notifications, Icons.Filled.Notifications),
        NavTabItem(TabType.Help, "nav.help", Icons.Outlined.Help, Icons.Filled.Help),
    )

    ClaySurface(
        color = CanvasLight.copy(alpha = 0.97f),
        modifier = modifier,
        shape = ClayShapes.card,
        depth = 12.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 4.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            tabs.forEach { tab ->
                val isActive = activeTab == tab.id
                val isSosIndicator = tab.id == TabType.Status && sosActive
                NavTile(
                    tab = tab,
                    isActive = isActive,
                    isSosIndicator = isSosIndicator,
                    onClick = { onTabChange(tab.id) }
                )
            }
        }
    }
}

@Composable
private fun NavTile(
    tab: NavTabItem,
    isActive: Boolean,
    isSosIndicator: Boolean,
    onClick: () -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by interactionSource.collectIsPressedAsState()

    ClaySurface(
        color = if (isActive) PrimaryGreen else ClayCreamTint,
        modifier = Modifier
            .width(52.dp)
            .graphicsLayer {
                scaleX = if (pressed) 0.9f else 1f
                scaleY = if (pressed) 0.9f else 1f
            },
        shape = ClayShapes.control,
        depth = if (isActive) 6.dp else 3.dp,
        tint = if (isActive) null else BorderLight.copy(alpha = 0.5f),
        contentColor = if (isActive) CanvasLight else TextSecondaryLight,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier
                .padding(vertical = 6.dp)
                .fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier.fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = if (isActive) tab.activeIcon else tab.icon,
                    contentDescription = T(tab.labelKey),
                    tint = if (isActive) CanvasLight else TextSecondaryLight,
                    modifier = Modifier.size(if (isActive) 24.dp else 20.dp)
                )
                if (isSosIndicator) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .offset(x = -2.dp, y = 2.dp)
                            .size(9.dp)
                            .clip(CircleShape)
                            .background(EmergencyRed)
                    )
                }
            }
            Spacer(Modifier.height(3.dp))
            Text(
                T(tab.labelKey),
                style = MaterialTheme.typography.labelSmall.copy(
                    fontSize = 6.sp,
                    letterSpacing = 0.sp
                ),
                color = if (isActive) CanvasLight.copy(alpha = 0.9f) else TextSecondaryLight,
                textAlign = TextAlign.Center,
                maxLines = 1
            )
        }
    }
}