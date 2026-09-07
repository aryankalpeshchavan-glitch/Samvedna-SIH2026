package com.crisiscore.app.data.model

import kotlinx.serialization.Serializable

enum class SosState {
    IDLE, SOS_CONFIRMATION, SENDING, SENT, OFFLINE_QUEUED, ERROR,
    VERIFIED, ASSIGNED, VOLUNTEER_EN_ROUTE, HELP_ARRIVED, RESOLVED
}

enum class IncidentCategory {
    LANDSLIDE, SLOPE_CRACK, ROAD_BLOCKED, FLOOD,
    BUILDING_DAMAGE, PERSON_TRAPPED, OTHER
}

enum class SeverityLevel { LOW, WATCH, MEDIUM, HIGH, CRITICAL }

@Serializable
data class LocationData(
    val latitude: Double? = null,
    val longitude: Double? = null,
    val accuracy: Double? = null,
    val addressName: String? = null,
    val status: String = "LOCATION_UNAVAILABLE",
    val timestamp: Long? = null,
    val isFallbackLocation: Boolean = false
)

@Serializable
data class SosPayload(
    val sosId: String,
    val timestamp: Long,
    val location: LocationData,
    val incidentType: String? = null,
    val note: String? = null,
    val networkStatusOnTrigger: String,
    val dataSource: String = "synthetic"
)

@Serializable
data class IncidentReportPayload(
    val id: String,
    val category: String,
    val severity: String,
    val description: String? = null,
    val location: LocationData,
    val timestamp: Long
)

data class SosStatusDetail(
    val state: SosState = SosState.IDLE,
    val sosId: String? = null,
    val timestamp: Long? = null,
    val assignedVolunteerName: String? = null,
    val assignedVolunteerPhone: String? = null,
    val etaMinutes: Int? = null,
    val lastUpdatedText: String? = null,
    val errorMessage: String? = null
)

data class FamilyMember(
    val id: String,
    val name: String,
    val relationship: String,
    val status: FamilyMemberStatus = FamilyMemberStatus.NEEDS_CHECKIN,
    val checkedInBy: String? = null,
    val checkedInAt: String? = null,
    val location: String? = null,
    val isSelf: Boolean = false
)

enum class FamilyMemberStatus { CHECKED_IN, NEEDS_CHECKIN, UNVERIFIED }

data class Helpline(
    val title: String,
    val number: String,
    val altNumber: String,
    val description: String,
    val badge: String,
    val colorType: HelplineColorType
)

enum class HelplineColorType { RED, GREEN, AMBER }

data class Alert(
    val id: String,
    val title: String,
    val body: String,
    val level: SeverityLevel,
    val issuedAgo: String,
    val source: String
)

// API Request/Response models
@Serializable
data class RegisterRequest(
    val phone: String,
    val password: String,
    val name: String,
    val role: String = "citizen"
)

@Serializable
data class LoginRequest(
    val phone: String,
    val password: String
)

@Serializable
data class AuthResponse(
    val access_token: String? = null,
    val token_type: String? = null
)

@Serializable
data class IncidentRequest(
    val type: String,
    val description: String,
    val lat: Double,
    val lng: Double,
    val severity: Int,
    val idempotency_key: String
)

@Serializable
data class IncidentResponse(
    val id: String? = null,
    val status: String? = null
)

@Serializable
data class RiskZone(
    val zone_id: String? = null,
    val name: String? = null,
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val risk_score: Double = 0.0,
    val risk_level: String = "LOW",
    val data_status: String = "unavailable"
)

// Decision endpoint models
@Serializable
data class DecisionRequest(
    val lat: Double,
    val lng: Double
)

@Serializable
data class DecisionResponse(
    val risk: String,           // LOW, WATCH, MEDIUM, HIGH, CRITICAL
    val confidence: Double,     // 0.0 - 1.0
    val drivers: List<String>,  // Explanation factors
    val actions: List<String>,  // Recommended actions
    val data_status: String,    // live, synthetic, replayed
    val freshness: String,      // ISO8601 timestamp
    val explanation: String? = null
)

// Risk explanation
@Serializable
data class RiskExplanation(
    val zone_id: String,
    val risk: String,
    val confidence: Double,
    val drivers: List<String>,
    val actions: List<String>,
    val freshness: String
)

// Sync endpoints
@Serializable
data class SyncIncidentsRequest(
    val incidents: List<IncidentRequest>
)

@Serializable
data class SyncIncidentsResponse(
    val synced: List<SyncedIncident>,
    val failed: List<FailedIncident>
)

@Serializable
data class SyncedIncident(
    val idempotency_key: String,
    val incident_id: String,
    val status: String
)

@Serializable
data class FailedIncident(
    val idempotency_key: String,
    val error: String
)

// Incident detail for tracking
@Serializable
data class IncidentDetail(
    val id: String,
    val type: String,
    val description: String,
    val lat: Double,
    val lng: Double,
    val severity: Int,
    val status: String,         // submitted, verified, assigned, responding, resolved
    val created_at: String,
    val updated_at: String,
    val citizen_id: String,
    val assigned_volunteer: AssignedVolunteer? = null
)

@Serializable
data class AssignedVolunteer(
    val name: String,
    val phone: String,
    val eta_minutes: Int? = null
)

// Notifications
@Serializable
data class Notification(
    val id: String,
    val title: String,
    val body: String,
    val type: String,           // incident_update, alert, system
    val incident_id: String? = null,
    val created_at: String,
    val read: Boolean = false
)