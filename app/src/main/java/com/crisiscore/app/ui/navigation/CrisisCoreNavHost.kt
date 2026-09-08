package com.crisiscore.app.ui.navigation

import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.crisiscore.app.data.model.Alert
import com.crisiscore.app.data.model.SeverityLevel
import com.crisiscore.app.data.model.SosState
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.screens.alerts.AlertsScreen
import com.crisiscore.app.ui.screens.auth.AuthScreen
import com.crisiscore.app.ui.screens.family.FamilyScreen
import com.crisiscore.app.ui.screens.help.HelpScreen
import com.crisiscore.app.ui.screens.home.HomeScreen
import com.crisiscore.app.ui.screens.incident.IncidentScreen
import com.crisiscore.app.ui.screens.status.StatusScreen
import com.crisiscore.app.ui.viewmodel.AppViewModel
import com.crisiscore.app.util.T

@Composable
fun CrisisCoreNavHost(
    viewModel: AppViewModel = viewModel()
) {
    val activeTab by viewModel.activeTab.collectAsState()
    val sosState by viewModel.sosState.collectAsState()
    val sosDetail by viewModel.sosDetail.collectAsState()
    val notifications by viewModel.notifications.collectAsState()
    var showAuth by remember { mutableStateOf(false) }

    val tabOrder = remember {
        listOf(TabType.Home, TabType.Incident, TabType.Status, TabType.Family, TabType.Alerts, TabType.Help)
    }

    val alertsList = remember(notifications) {
        if (notifications.isNotEmpty()) {
            notifications.map { notif ->
                Alert(
                    id = notif.id,
                    title = notif.title,
                    body = notif.body,
                    level = when (notif.type.lowercase()) {
                        "critical" -> SeverityLevel.CRITICAL
                        "alert", "warning" -> SeverityLevel.HIGH
                        else -> SeverityLevel.WATCH
                    },
                    issuedAgo = notif.created_at.ifBlank { "Recent" },
                    source = "Disaster Management Authority"
                )
            }
        } else {
            listOf(
                Alert(
                    id = "alert-1",
                    title = T.get("alerts.sample1.title"),
                    body = T.get("alerts.sample1.body"),
                    level = SeverityLevel.CRITICAL,
                    issuedAgo = T.get("alerts.sample1.issuedAgo"),
                    source = T.get("alerts.sample1.source")
                ),
                Alert(
                    id = "alert-2",
                    title = T.get("alerts.sample2.title"),
                    body = T.get("alerts.sample2.body"),
                    level = SeverityLevel.HIGH,
                    issuedAgo = T.get("alerts.sample2.issuedAgo"),
                    source = T.get("alerts.sample2.source")
                )
            )
        }
    }

    if (showAuth) {
        AuthScreen(
            repository = viewModel.repository,
            onLoginSuccess = { showAuth = false }
        )
        return
    }

    Box(modifier = Modifier.fillMaxSize()) {
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            topBar = {
                Column {
                    AppHeader(
                        onHelpClick = { viewModel.setActiveTab(TabType.Help) }
                    )
                    OfflineBanner()
                }
            },
            bottomBar = {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Spacer(Modifier.navigationBarsPadding())
                    BottomNavBar(
                        activeTab = activeTab,
                        onTabChange = { viewModel.setActiveTab(it) },
                        sosActive = sosState != SosState.IDLE,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
            }
        ) { padding ->
            Box(modifier = Modifier.padding(padding)) {
                AnimatedContent(
                    targetState = activeTab,
                    transitionSpec = {
                        val fromIndex = tabOrder.indexOf(initialState)
                        val toIndex = tabOrder.indexOf(targetState)
                        val dir = if (toIndex >= fromIndex) 1 else -1
                        slideInHorizontally(tween(220)) { it * dir / 4 } + fadeIn(tween(220)) togetherWith
                        slideOutHorizontally(tween(180)) { -it * dir / 4 } + fadeOut(tween(180))
                    },
                    label = "tabTransition"
                ) { tab ->
                    when (tab) {
                        TabType.Home -> HomeScreen(
                            repository = viewModel.repository,
                            onTriggerSos = { viewModel.triggerSos() },
                            onNavigate = { viewModel.setActiveTab(it) },
                            onAuthClick = { showAuth = true }
                        )
                        TabType.Incident -> IncidentScreen(
                            repository = viewModel.repository,
                            onSubmit = { _, _, _ ->
                                viewModel.loadNotifications()
                            }
                        )
                        TabType.Status -> StatusScreen(
                            sosState = sosState,
                            sosDetail = sosDetail,
                            onReset = { viewModel.resetSos() }
                        )
                        TabType.Family -> FamilyScreen()
                        TabType.Alerts -> AlertsScreen(alerts = alertsList)
                        TabType.Help -> HelpScreen()
                    }
                }
            }
        }

        // Overlay dialog outside of bottomBar to ensure correct Z-order and touch handling
        if (sosState == SosState.SOS_CONFIRMATION) {
            SosConfirmDialog(
                onConfirm = { viewModel.confirmSos(it) },
                onDismiss = { viewModel.cancelSos() }
            )
        }
    }
}
