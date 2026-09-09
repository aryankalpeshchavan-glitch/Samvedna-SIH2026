package com.crisiscore.app.data.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive

enum class SosState {
    IDLE, SOS_CONFIRMATION, SENDING, SENT, OFFLINE_QUEUED, ERROR,
    VERIFIED, ASSIGNED, VOLUNTEER_EN_ROUTE, HELP_ARRIVED, RESOLVED
}

enum class IncidentCategory {
    LANDSLIDE, SLOPE_CRACK, ROAD_BLOCKED, FLOOD, FLASH_FLOOD,
    BUILDING_DAMAGE, PERSON_TRAPPED, MEDICAL_EMERGENCY, FIRE, OTHER
}

enum class SeverityLevel { LOW, WATCH, MEDIUM, HIGH, CRITICAL }

enum class NetworkStatus { ONLINE, WEAK, OFFLINE }

enum class LocationStatus {
    LOCATION_DETECTED, LOCATION_UNAVAILABLE, REQUESTING_LOCATION, PERMISSION_DENIED
}

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
    val dataSource: String = "live"
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

data class CommunitySafetyReport(
    val id: String,
    val name: String? = null,
    val context: String,
    val location: String,
    val timestamp: String
)

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
    val token_type: String? = null,
    val role: String? = null
)

@Serializable
data class IncidentRequest(
    val type: String,
    val description: String,
    val lat: Double,
    val lng: Double,
    val severity: Int,
    val photo_url: String? = null,
    val idempotency_key: String? = null,
    val data_label: String? = "live"
)

@Serializable
data class IncidentResponse(
    val id: String? = null,
    val reporter_id: Int? = null,
    val type: String? = null,
    val description: String? = null,
    val lat: Double? = null,
    val lng: Double? = null,
    val severity: Int? = null,
    val status: String? = null,
    val data_label: String? = null,
    val photo_url: String? = null,
    val idempotency_key: String? = null,
    val created_at: String? = null,
    val updated_at: String? = null
)

@Serializable
data class IncidentBatchSyncRequest(
    val items: List<IncidentRequest>
)

@Serializable
data class IncidentBatchSyncResponse(
    val synced: List<IncidentResponse> = emptyList(),
    val duplicates: List<IncidentResponse> = emptyList(),
    val errors: List<Map<String, String>> = emptyList()
)

@Serializable
data class StatusResponse(
    val incident_id: String? = null,
    val status: String? = null,
    val severity: Int? = null,
    val assignment: AssignmentData? = null,
    val updated_at: String? = null
)

@Serializable
data class AssignmentData(
    val id: String? = null,
    val volunteer_id: Int? = null,
    val volunteer_name: String? = null,
    val volunteer_phone: String? = null,
    val status: String? = null,
    val sla_deadline: String? = null,
    val eta_minutes: Int? = null
)

@Serializable
data class RiskZone(
    @SerialName("id")
    val id: String? = null,
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val risk_score: Double = 0.0,
    val risk_level: String = "LOW",
    @SerialName("data_label")
    val data_status: String = "live",
    val horizon_hours: Int = 24,
    val confidence: Double? = null,
    val state: String? = null
) {
    val zone_id: String? get() = id
    val data_label: String get() = data_status
}

@Serializable
data class DecisionRequest(
    val lat: Double,
    val lng: Double,
    val zone_id: String? = null,
    val horizon: String = "24h"
)

@Serializable
data class DriverExplanation(
    val key: String,
    val label: String,
    val description: String,
    val unit: String? = null,
    val category: String = "hydrology",
    val value: Double? = null
)

val List<DriverExplanation>.summary: String?
    get() = firstOrNull()?.description

val List<DriverExplanation>.narrative: String?
    get() = if (size > 1) drop(1).joinToString("\n") { "${it.label}: ${it.description}" }.ifEmpty { null } else null

@Serializable
data class RiskSummary(
    val risk_score: Double = 0.0,
    val risk_level: String = "LOW",
    val confidence: Double = 0.9,
    val drivers: List<String> = emptyList(),
    val data_status: String = "live"
) {
    val top_drivers: List<String> get() = drivers
    val data_label: String get() = data_status
}

@Serializable
data class PriorityResult(
    val priority_score: Double = 0.0,
    val priority_level: String = "LOW",
    val weights: Map<String, Double> = emptyMap(),
    val factors: Map<String, Double> = emptyMap()
)

@Serializable
data class DecisionResponse(
    val location_id: String? = null,
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val risk: RiskSummary = RiskSummary(),
    val explanation: List<DriverExplanation> = emptyList(),
    val priority: PriorityResult? = null,
    val actions: List<String> = emptyList(),
    val data_status: String = "live",
    val computed_at: String? = null
)

@Serializable
data class RiskExplainResponse(
    val zone_id: String,
    val risk_score: Double = 0.0,
    val explanation: String = "",
    val risk_level: String = "LOW"
)

@Serializable
data class NotificationLogOut(
    val id: String,
    val incident_id: String? = null,
    val recipient_id: Int? = null,
    val channel: String = "in_app",
    val status: String = "delivered",
    val data_label: String = "live",
    val payload: Map<String, JsonElement> = emptyMap(),
    @SerialName("message")
    private val rawMessage: String? = null,
    @SerialName("priority")
    private val rawPriority: String? = null,
    val error_message: String? = null,
    val sent_at: String? = null
) {
    val message: String
        get() = rawMessage
            ?: (payload["message"] as? JsonPrimitive)?.content
            ?: payload["message"]?.toString()?.trim('"')
            ?: ""

    val priority: String
        get() = rawPriority
            ?: (payload["priority"] as? JsonPrimitive)?.content
            ?: payload["priority"]?.toString()?.trim('"')
            ?: "MEDIUM"
}

@Serializable
data class HealthResponse(
    val status: String? = null
)
