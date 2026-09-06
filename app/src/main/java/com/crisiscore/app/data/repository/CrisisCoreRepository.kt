package com.crisiscore.app.data.repository

import android.content.Context
import android.location.Location
import android.util.Log
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.model.*
import com.crisiscore.app.data.local.CrisisCoreDatabase
import com.crisiscore.app.data.local.PendingIncidentEntity
import com.crisiscore.app.data.local.PendingSosEntity
import com.crisiscore.app.data.local.SecurePreferences
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class CrisisCoreRepository(private val context: Context) {
    private val api = RetrofitClient.getApi()
    private val db = CrisisCoreDatabase.getInstance(context)
    private val dao = db.offlineDao()
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private val locationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)

    suspend fun register(phone: String, password: String, name: String): Boolean = withContext(Dispatchers.IO) {
        try {
            api.register(RegisterRequest(phone, password, name)).isSuccessful
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Register failed", e)
            false
        }
    }

    suspend fun login(phone: String, password: String): String? = withContext(Dispatchers.IO) {
        try {
            val res = api.login(LoginRequest(phone, password))
            if (res.isSuccessful) {
                val token = res.body()?.access_token
                token?.let { SecurePreferences.setToken(it) }
                token
            } else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Login failed", e)
            null
        }
    }

    suspend fun autoLoginDemo(): String? {
        var phone = SecurePreferences.getDemoPhone()
        if (phone == null) {
            phone = "+91${(1000000000..9999999999).random()}"
            SecurePreferences.setDemoPhone(phone)
        }
        register(phone, "demoPass123", "Citizen Demo")
        return login(phone, "demoPass123")
    }

    suspend fun createIncident(type: String, description: String, lat: Double, lng: Double, severity: Int): IncidentResponse? = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) autoLoginDemo()
            val res = api.createIncident(IncidentRequest(type, description, lat, lng, severity))
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Create incident failed", e)
            null
        }
    }

    suspend fun getStatus(incidentId: String): StatusResponse? = withContext(Dispatchers.IO) {
        try {
            val res = api.getStatus(incidentId)
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get status failed", e)
            null
        }
    }

    @Suppress("MissingPermission")
    suspend fun getCurrentLocation(): LocationData = withContext(Dispatchers.IO) {
        try {
            val loc = suspendCancellableCoroutine<Location?> { cont ->
                val cts = CancellationTokenSource()
                cont.invokeOnCancellation { cts.cancel() }
                locationClient.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, cts.token)
                    .addOnSuccessListener { loc -> if (cont.isActive) cont.resume(loc) }
                    .addOnFailureListener { if (cont.isActive) cont.resumeWithException(it) }
            }
            LocationData(
                latitude = loc?.latitude,
                longitude = loc?.longitude,
                accuracy = loc?.accuracy?.toDouble(),
                status = "LOCATION_DETECTED",
                timestamp = System.currentTimeMillis()
            )
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Location unavailable, using fallback", e)
            LocationData(
                latitude = null,
                longitude = null,
                status = "LOCATION_UNAVAILABLE",
                isFallbackLocation = true
            )
        }
    }

    suspend fun getHealth(): Boolean = withContext(Dispatchers.IO) {
        try { api.getHealth().isSuccessful } catch (e: Exception) { false }
    }

    suspend fun savePendingSos(payload: SosPayload) {
        dao.insertSos(PendingSosEntity(
            id = payload.sosId,
            payloadJson = json.encodeToString(payload),
            createdAt = System.currentTimeMillis()
        ))
    }

    fun getPendingSos(): Flow<List<PendingSosEntity>> = dao.getAllSos()

    suspend fun markSosSynced(id: String) = dao.markSosSynced(id)

    suspend fun savePendingIncident(payload: IncidentReportPayload) {
        dao.insertIncident(PendingIncidentEntity(
            id = payload.id,
            payloadJson = json.encodeToString(payload),
            createdAt = System.currentTimeMillis()
        ))
    }

    fun getPendingIncidents(): Flow<List<PendingIncidentEntity>> = dao.getAllIncidents()
}
