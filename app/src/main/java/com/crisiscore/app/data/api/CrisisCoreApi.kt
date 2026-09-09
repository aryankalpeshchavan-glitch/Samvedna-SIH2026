package com.crisiscore.app.data.api

import com.crisiscore.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface CrisisCoreApi {
    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<Unit>

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>

    @POST("incidents")
    suspend fun createIncident(@Body request: IncidentRequest): Response<IncidentResponse>

    @POST("incidents/sync")
    suspend fun syncIncidents(@Body request: IncidentBatchSyncRequest): Response<IncidentBatchSyncResponse>

    @GET("incidents/{id}")
    suspend fun getIncident(@Path("id") incidentId: String): Response<IncidentResponse>

    @GET("status/{id}")
    suspend fun getStatus(@Path("id") incidentId: String): Response<StatusResponse>

    @GET("risk")
    suspend fun getRisk(
        @Query("bbox") bbox: String? = null,
        @Query("horizon") horizon: String = "24h"
    ): Response<List<RiskZone>>

    @GET("risk/{zone_id}/explain")
    suspend fun getRiskExplain(@Path("zone_id") zoneId: String): Response<RiskExplainResponse>

    @POST("intelligence/decision")
    suspend fun getDecision(@Body request: DecisionRequest): Response<DecisionResponse>

    @GET("notifications")
    suspend fun getNotifications(@Query("limit") limit: Int = 50): Response<List<NotificationLogOut>>

    @GET("health")
    suspend fun getHealth(): Response<HealthResponse>
}
