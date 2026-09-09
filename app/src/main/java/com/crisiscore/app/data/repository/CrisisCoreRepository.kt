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
import java.util.UUID
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
            api.register(RegisterRequest(phone = phone, password = password, name = name, role = "citizen")).isSuccessful
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Register failed", e)
            false
        }
    }

    suspend fun login(phone: String, password: String): String? = withContext(Dispatchers.IO) {
        try {
            val res = api.login(LoginRequest(phone = phone, password = password))
            if (res.isSuccessful) {
                val token = res.body()?.access_token
                token?.let { SecurePreferences.setToken(it) }
                token
            } else {
                Log.w("CrisisCoreRepo", "Login failed with code: ${res.code()}")
                null
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Login failed", e)
            null
        }
    }

    fun isAuthenticated(): Boolean = SecurePreferences.getToken() != null

    fun logout() {
        SecurePreferences.setToken(null)
    }

    suspend fun createIncident(
        type: String,
        description: String,
        lat: Double,
        lng: Double,
        severity: Int,
        photoUrl: String? = null,
        idempotencyKey: String? = null
    ): IncidentResponse? = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "createIncident: No JWT token found. Authentication required.")
                return@withContext null
            }
            val safeKey = idempotencyKey ?: UUID.randomUUID().toString()
            val safeType = mapCategoryToBackendType(type)
            val safeSeverity = severity.coerceIn(1, 5)

            val request = IncidentRequest(
                type = safeType,
                description = description,
                lat = lat,
                lng = lng,
                severity = safeSeverity,
                photo_url = photoUrl,
                idempotency_key = safeKey,
                data_label = "live"
            )
            val res = api.createIncident(request)
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on createIncident. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext null
            }
            if (res.isSuccessful) {
                val body = res.body()
                Log.i("CrisisCoreRepo", "Incident created successfully on backend: ${body?.id}")
                body
            } else {
                val err = res.errorBody()?.string()
                Log.w("CrisisCoreRepo", "Create incident returned code: ${res.code()}, body: $err")
                null
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Create incident network failure", e)
            null
        }
    }

    suspend fun getStatus(incidentId: String): StatusResponse? = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "getStatus: No JWT token found. Authentication required.")
                return@withContext null
            }
            val res = api.getStatus(incidentId)
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on getStatus. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext null
            }
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get status failed", e)
            null
        }
    }

    suspend fun getIncident(id: String): IncidentResponse? = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "getIncident: No JWT token found. Authentication required.")
                return@withContext null
            }
            val res = api.getIncident(id)
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on getIncident. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext null
            }
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get incident failed", e)
            null
        }
    }

    suspend fun getRiskZones(horizon: String = "24h"): List<RiskZone> = withContext(Dispatchers.IO) {
        try {
            val res = api.getRisk(horizon = horizon)
            if (res.isSuccessful) res.body().orEmpty() else emptyList()
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get risk zones failed", e)
            emptyList()
        }
    }

    suspend fun getDecision(
        lat: Double,
        lng: Double,
        zoneId: String? = null,
        horizon: String = "24h"
    ): DecisionResponse? = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "getDecision: No JWT token found. Authentication required.")
                return@withContext null
            }
            val res = api.getDecision(DecisionRequest(lat = lat, lng = lng, zone_id = zoneId, horizon = horizon))
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on getDecision. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext null
            }
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get decision failed", e)
            null
        }
    }

    suspend fun getRiskExplain(zoneId: String): RiskExplainResponse? = withContext(Dispatchers.IO) {
        try {
            val res = api.getRiskExplain(zoneId)
            if (res.isSuccessful) res.body() else null
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get risk explain failed", e)
            null
        }
    }

    suspend fun getNotifications(): List<NotificationLogOut> = withContext(Dispatchers.IO) {
        try {
            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "getNotifications: No JWT token found. Authentication required.")
                return@withContext emptyList()
            }
            val res = api.getNotifications()
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on getNotifications. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext emptyList()
            }
            if (res.isSuccessful) res.body().orEmpty() else emptyList()
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get notifications failed", e)
            emptyList()
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
                latitude = 26.1445,
                longitude = 91.7362,
                status = "LOCATION_UNAVAILABLE",
                isFallbackLocation = true
            )
        }
    }

    suspend fun getHealth(): Boolean = withContext(Dispatchers.IO) {
        try { api.getHealth().isSuccessful } catch (e: Exception) { false }
    }

    suspend fun savePendingSos(payload: SosPayload) = withContext(Dispatchers.IO) {
        dao.insertSos(PendingSosEntity(
            id = payload.sosId,
            payloadJson = json.encodeToString(payload),
            createdAt = System.currentTimeMillis()
        ))
    }

    fun getPendingSos(): Flow<List<PendingSosEntity>> = dao.getAllSos()

    suspend fun markSosSynced(id: String) = withContext(Dispatchers.IO) { dao.markSosSynced(id) }

    suspend fun savePendingIncident(payload: IncidentReportPayload) = withContext(Dispatchers.IO) {
        dao.insertIncident(PendingIncidentEntity(
            id = payload.id,
            payloadJson = json.encodeToString(payload),
            createdAt = System.currentTimeMillis()
        ))
    }

    fun getPendingIncidents(): Flow<List<PendingIncidentEntity>> = dao.getAllIncidents()

    suspend fun syncOfflineIncidents(): Boolean = withContext(Dispatchers.IO) {
        try {
            val pendingIncidents = dao.getUnsyncedIncidents()
            val pendingSos = dao.getUnsyncedSos()

            if (pendingIncidents.isEmpty() && pendingSos.isEmpty()) {
                return@withContext true
            }

            val requestList = mutableListOf<IncidentRequest>()

            val incidentIds = mutableListOf<String>()
            for (entity in pendingIncidents) {
                try {
                    val report = json.decodeFromString<IncidentReportPayload>(entity.payloadJson)
                    requestList.add(
                        IncidentRequest(
                            type = mapCategoryToBackendType(report.category),
                            description = report.description?.ifBlank { null } ?: "Incident report (${report.category})",
                            lat = report.location.latitude ?: 26.1445,
                            lng = report.location.longitude ?: 91.7362,
                            severity = mapSeverityToBackendInt(report.severity),
                            idempotency_key = report.id,
                            data_label = "live"
                        )
                    )
                    incidentIds.add(entity.id)
                } catch (e: Exception) {
                    Log.e("CrisisCoreRepo", "Failed to deserialize pending incident ${entity.id}", e)
                }
            }

            val sosIds = mutableListOf<String>()
            for (entity in pendingSos) {
                try {
                    val sos = json.decodeFromString<SosPayload>(entity.payloadJson)
                    requestList.add(
                        IncidentRequest(
                            type = sos.incidentType?.let { mapCategoryToBackendType(it) } ?: "other",
                            description = sos.note?.ifBlank { null } ?: "EMERGENCY SOS SIGNAL",
                            lat = sos.location.latitude ?: 26.1445,
                            lng = sos.location.longitude ?: 91.7362,
                            severity = 5,
                            idempotency_key = sos.sosId,
                            data_label = "live"
                        )
                    )
                    sosIds.add(entity.id)
                } catch (e: Exception) {
                    Log.e("CrisisCoreRepo", "Failed to deserialize pending SOS ${entity.id}", e)
                }
            }

            if (requestList.isEmpty()) {
                return@withContext true
            }

            if (SecurePreferences.getToken() == null) {
                Log.w("CrisisCoreRepo", "syncOfflineIncidents: No JWT token found. Authentication required.")
                return@withContext false
            }

            val res = api.syncIncidents(IncidentBatchSyncRequest(items = requestList))
            if (res.code() == 401) {
                Log.w("CrisisCoreRepo", "401 Unauthorized on syncIncidents. Clearing invalid token.")
                SecurePreferences.setToken(null)
                return@withContext false
            }
            if (res.isSuccessful) {
                for (id in incidentIds) {
                    dao.markIncidentSynced(id)
                }
                for (id in sosIds) {
                    dao.markSosSynced(id)
                }
                true
            } else {
                Log.w("CrisisCoreRepo", "Batch sync failed with code ${res.code()}")
                false
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "syncOfflineIncidents failed", e)
            false
        }
    }

    companion object {
        fun mapCategoryToBackendType(category: String): String {
            return when (category.uppercase()) {
                "LANDSLIDE", "SLOPE_CRACK", "ROAD_BLOCKED" -> "landslide"
                "FLOOD", "FLASH_FLOOD" -> "flood"
                "FIRE" -> "fire"
                "EARTHQUAKE", "BUILDING_DAMAGE" -> "earthquake"
                else -> "other"
            }
        }

        fun mapSeverityToBackendInt(severity: String): Int {
            return when (severity.uppercase()) {
                "CRITICAL" -> 5
                "HIGH" -> 4
                "MEDIUM", "WATCH" -> 3
                "LOW" -> 1
                else -> 3
            }
        }
    }
}
