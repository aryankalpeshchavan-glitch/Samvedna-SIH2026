package com.crisiscore.app.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.crisiscore.app.CrisisCoreApp
import com.crisiscore.app.data.api.WsEvent
import com.crisiscore.app.data.model.*
import com.crisiscore.app.ui.components.TabType
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class AppViewModel(application: Application) : AndroidViewModel(application) {
    val repository = (application as? CrisisCoreApp)?.repository
        ?: com.crisiscore.app.data.repository.CrisisCoreRepository(application)

    private val _sosState = MutableStateFlow(SosState.IDLE)
    val sosState: StateFlow<SosState> = _sosState.asStateFlow()

    private val _sosDetail = MutableStateFlow(SosStatusDetail())
    val sosDetail: StateFlow<SosStatusDetail> = _sosDetail.asStateFlow()

    private val _notifications = MutableStateFlow<List<Notification>>(emptyList())
    val notifications: StateFlow<List<Notification>> = _notifications.asStateFlow()

    private val _incidents = MutableStateFlow<List<IncidentOut>>(emptyList())
    val incidents: StateFlow<List<IncidentOut>> = _incidents.asStateFlow()

    private val _isRefreshingIncidents = MutableStateFlow(false)
    val isRefreshingIncidents: StateFlow<Boolean> = _isRefreshingIncidents.asStateFlow()

    private val _activeTab = MutableStateFlow(TabType.Home)
    val activeTab: StateFlow<TabType> = _activeTab.asStateFlow()

    private val _isEmergencyMode = MutableStateFlow(false)
    val isEmergencyMode: StateFlow<Boolean> = _isEmergencyMode.asStateFlow()

    init {
        // Collect WebSocket events in viewModelScope
        viewModelScope.launch {
            repository.getWebSocketEvents().collect { event ->
                when (event) {
                    is WsEvent.NotificationEvent -> {
                        _notifications.value = listOf(event.notification) + _notifications.value
                    }
                    is WsEvent.IncidentUpdateEvent -> {
                        val newSosState = when (event.status.uppercase()) {
                            "VERIFIED" -> SosState.VERIFIED
                            "ASSIGNED" -> SosState.ASSIGNED
                            "EN_ROUTE", "VOLUNTEER_EN_ROUTE" -> SosState.VOLUNTEER_EN_ROUTE
                            "RESOLVED" -> SosState.RESOLVED
                            "HELP_ARRIVED" -> SosState.HELP_ARRIVED
                            else -> _sosState.value
                        }
                        _sosState.value = newSosState
                        _sosDetail.value = _sosDetail.value.copy(
                            state = newSosState,
                            sosId = event.incidentId,
                            assignedVolunteerName = event.volunteerName ?: _sosDetail.value.assignedVolunteerName,
                            assignedVolunteerPhone = event.volunteerPhone ?: _sosDetail.value.assignedVolunteerPhone,
                            etaMinutes = event.etaMinutes ?: _sosDetail.value.etaMinutes
                        )
                        // Trigger immediate incident list refresh on map
                        loadIncidents()
                    }
                    is WsEvent.IncidentsChanged -> {
                        loadIncidents()
                    }
                    is WsEvent.Connected -> {
                        loadNotifications()
                        loadIncidents()
                    }
                    else -> Unit
                }
            }
        }
        loadNotifications()
        loadIncidents()

        // Periodic polling to guarantee Swagger updates reflect on map even without WS
        viewModelScope.launch {
            while (isActive) {
                kotlinx.coroutines.delay(10000L)
                val list = repository.getIncidents()
                if (list.isNotEmpty()) {
                    _incidents.value = list
                }
            }
        }
    }

    fun loadIncidents() {
        viewModelScope.launch {
            _isRefreshingIncidents.value = true
            val list = repository.getIncidents()
            if (list.isNotEmpty()) {
                _incidents.value = list
            }
            _isRefreshingIncidents.value = false
        }
    }

    fun addIncident(incident: IncidentOut) {
        _incidents.value = listOf(incident) + _incidents.value.filter { it.id != incident.id }
    }

    fun setActiveTab(tab: TabType) {
        _activeTab.value = tab
    }

    fun toggleEmergencyMode() {
        _isEmergencyMode.value = !_isEmergencyMode.value
    }

    fun triggerSos() {
        _sosState.value = SosState.SOS_CONFIRMATION
    }

    fun cancelSos() {
        _sosState.value = SosState.IDLE
    }

    fun resetSos() {
        _sosState.value = SosState.IDLE
        _sosDetail.value = SosStatusDetail()
    }

    fun confirmSos(category: String?) {
        _sosState.value = SosState.SENDING
        _sosDetail.value = SosStatusDetail(
            state = SosState.SENDING,
            timestamp = System.currentTimeMillis()
        )
        _activeTab.value = TabType.Status

        viewModelScope.launch {
            val location = repository.getCurrentLocation()
            val lat = location.latitude ?: 26.1445
            val lng = location.longitude ?: 91.7362
            val catName = category ?: "EMERGENCY_SOS"

            val response = repository.createIncident(
                type = catName,
                description = "Emergency SOS request triggered for $catName",
                lat = lat,
                lng = lng,
                severity = 5
            )

            if (response != null && response.status != "QUEUED_OFFLINE") {
                _sosState.value = SosState.SENT
                _sosDetail.value = _sosDetail.value.copy(
                    state = SosState.SENT,
                    sosId = response.id ?: "SOS-${System.currentTimeMillis() % 10000}",
                    lastUpdatedText = "Signal received by CrisisCore relay"
                )
            } else {
                _sosState.value = SosState.OFFLINE_QUEUED
                _sosDetail.value = _sosDetail.value.copy(
                    state = SosState.OFFLINE_QUEUED,
                    sosId = response?.id ?: "OFFLINE-${System.currentTimeMillis() % 10000}",
                    lastUpdatedText = "Saved locally. Auto-sync on reconnect."
                )
            }
        }
    }

    suspend fun submitIncidentReport(
        category: IncidentCategory,
        severity: SeverityLevel,
        description: String,
        location: LocationData?
    ): IncidentOut? {
        val lat = location?.latitude ?: 26.1445
        val lng = location?.longitude ?: 91.7362
        val severityInt = when (severity) {
            SeverityLevel.LOW -> 1
            SeverityLevel.WATCH -> 2
            SeverityLevel.MEDIUM -> 3
            SeverityLevel.HIGH -> 4
            SeverityLevel.CRITICAL -> 5
        }
        val res = repository.createIncident(
            type = category.name,
            description = description.ifBlank { "${category.name} reported" },
            lat = lat,
            lng = lng,
            severity = severityInt
        )
        loadIncidents()
        return res
    }

    fun loadNotifications() {
        viewModelScope.launch {
            val liveNotifs = repository.getNotifications()
            if (liveNotifs.isNotEmpty()) {
                _notifications.value = liveNotifs
            }
        }
    }
}
