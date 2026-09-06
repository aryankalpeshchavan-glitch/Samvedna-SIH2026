package com.crisiscore.app.ui.navigation

import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.crisiscore.app.data.model.SosState
import com.crisiscore.app.data.model.SosStatusDetail
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.screens.alerts.AlertsScreen
import com.crisiscore.app.ui.screens.auth.AuthScreen
import com.crisiscore.app.ui.screens.family.FamilyScreen
import com.crisiscore.app.ui.screens.help.HelpScreen
import com.crisiscore.app.ui.screens.home.HomeScreen
import com.crisiscore.app.ui.screens.incident.IncidentScreen
import com.crisiscore.app.ui.screens.status.StatusScreen

@Composable
fun CrisisCoreNavHost() {
    val context = LocalContext.current
    val repository = remember { CrisisCoreRepository(context) }

    var activeTab by remember { mutableStateOf(TabType.Home) }
    var sosState by remember { mutableStateOf(SosState.IDLE) }
    var sosDetail by remember { mutableStateOf(SosStatusDetail()) }
    var showAuth by remember { mutableStateOf(false) }

    val triggerSos: () -> Unit = {
        sosState = SosState.SOS_CONFIRMATION
    }
    val confirmSos: (String?) -> Unit = { category ->
        sosState = SosState.SENDING
        sosDetail = sosDetail.copy(state = SosState.SENDING)
        activeTab = TabType.Status
    }
    val cancelSos: () -> Unit = {
        sosState = SosState.IDLE
    }
    val resetSos: () -> Unit = {
        sosState = SosState.IDLE
        sosDetail = SosStatusDetail()
    }

    if (showAuth) {
        AuthScreen(
            repository = repository,
            onLoginSuccess = { showAuth = false }
        )
        return
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            AppHeader(
                onHelpClick = { activeTab = TabType.Help }
            )
        },
        bottomBar = {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                if (sosState == SosState.SOS_CONFIRMATION) {
                    SosConfirmDialog(
                        onConfirm = { confirmSos(it) },
                        onDismiss = cancelSos
                    )
                }
                Spacer(Modifier.navigationBarsPadding())
                BottomNavBar(
                    activeTab = activeTab,
                    onTabChange = { activeTab = it },
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
                    fadeIn(tween(200)) + slideInVertically(tween(200)) togetherWith
                    fadeOut(tween(150)) + slideOutVertically(tween(150))
                },
                label = "tabTransition"
            ) { tab ->
                when (tab) {
                    TabType.Home -> HomeScreen(
                        repository = repository,
                        onTriggerSos = triggerSos,
                        onNavigate = { activeTab = it },
                        onAuthClick = { showAuth = true }
                    )
                    TabType.Incident -> IncidentScreen(
                        repository = repository,
                        onSubmit = { cat, _, _ ->
                            confirmSos(cat.name)
                        }
                    )
                    TabType.Status -> StatusScreen(
                        sosState = sosState,
                        sosDetail = sosDetail,
                        onReset = resetSos,
                        onSimulate = { sosState = it }
                    )
                    TabType.Family -> FamilyScreen()
                    TabType.Alerts -> AlertsScreen()
                    TabType.Help -> HelpScreen()
                }
            }
        }
    }
}
