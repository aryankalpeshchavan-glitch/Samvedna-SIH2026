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

    @GET("risk")
    suspend fun getRisk(@Query("bbox") bbox: String? = null): Response<List<RiskZone>>
}
