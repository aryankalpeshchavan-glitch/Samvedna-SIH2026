package com.crisiscore.app.data.api

import com.crisiscore.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface CrisisCoreApi {
    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<Unit>

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    // Intelligence / Decision endpoint for home risk
    @POST("intelligence/decision")
    suspend fun getDecision(@Body request: DecisionRequest): Response<DecisionResponse>

    // Risk endpoints
    @GET("risk")
    suspend fun getRiskZones(@Query("bbox") bbox: String? = null): Response<List<RiskZone>>

    @GET("risk/{zone_id}/explain")
    suspend fun getRiskExplanation(@Path("zone_id") zoneId: String): Response<RiskExplanation>

    // Incident endpoints
    @POST("incidents")
    suspend fun createIncident(@Body request: IncidentRequest): Response<IncidentResponse>

    @POST("incidents/sync")
    suspend fun syncIncidents(@Body request: SyncIncidentsRequest): Response<SyncIncidentsResponse>

    @GET("incidents/{incident_id}")
    suspend fun getIncident(@Path("incident_id") incidentId: String): Response<IncidentDetail>

    // Notifications
    @GET("notifications")
    suspend fun getNotifications(@Query("since") since: String? = null): Response<List<Notification>>
}