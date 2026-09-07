package com.crisiscore.app.data.repository

import android.content.Context
import android.location.Location
import com.google.android.gms.tasks.CancellationTokenSource
import android.util.Log
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.api.WebSocketClient
import com.crisiscore.app.data.local.OfflineDatabase
import com.crisiscore.app.data.local.PendingIncidentEntity
import com.crisiscore.app.data.local.SecurePreferences
import com.crisiscore.app.data.local.SyntheticRiskData
import com.crisiscore.app.data.model.*
import com.crisiscore.app.data.sync.SyncWorker
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class CrisisCoreRepository(private val context: Context) {
    private val api = RetrofitClient.getApi()
    private val db = OfflineDatabase.getInstance(context.applicationContext)
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private val locationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)
    private val workManager = WorkManager.getInstance(context)
    private val ws = WebSocketClient(context)

    init {
        CoroutineScope(Dispatchers.IO).launch { ws.connect() }
    }

    // ============================================================
    // Auth
    // ============================================================

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

    // ============================================================
    // Intelligence / Decision
    // ============================================================

    suspend fun getDecision(lat: Double, lng: Double): DecisionResponse = withContext(Dispatchers.IO) {
        try {
            val res = api.getDecision(DecisionRequest(lat, lng))
            if (res.isSuccessful) res.body() ?: DecisionResponse(
                risk = "UNKNOWN", confidence = 0.0, drivers = emptyList(),
                actions = emptyList(), data_status = "unavailable", freshness = ""
            ) else {
                DecisionResponse(
                    risk = "LOW", confidence = 1.0, drivers = listOf("using synthetic feed"),
                    actions = listOf("stay vigilant"), data_status = "synthetic", freshness = ""
                )
            }
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Decision feed unavailable, using synthetic", e)
            DecisionResponse(
                risk = "LOW", confidence = 1.0, drivers = listOf("using synthetic feed"),
                actions = listOf("stay vigilant"), data_status = "synthetic", freshness = ""
            )
        }
    }

    // ============================================================
    // Risk / Map
    // ============================================================

    suspend fun getRiskZones(): List<RiskZone> = withContext(Dispatchers.IO) {
        try {
            val res = api.getRiskZones()
            val live = if (res.isSuccessful) res.body().orEmpty() else emptyList()
            if (live.isNotEmpty()) live else SyntheticRiskData.zones()
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Risk feed unavailable, using synthetic", e)
            SyntheticRiskData.zones()
        }
    }

    suspend fun getRiskExplanation(zoneId: String): RiskExplanation = withContext(Dispatchers.IO) {
        try {
            val res = api.getRiskExplanation(zoneId)
            if (res.isSuccessful) res.body() ?: SyntheticRiskData.explanation(zoneId)
            else SyntheticRiskData.explanation(zoneId)
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Risk explanation unavailable", e)
            SyntheticRiskData.explanation(zoneId)
        }
    }

    // ============================================================
    // Incident / SOS / Reports
    // ============================================================

    private val incidentIdempotencyKey: String
        get() = "${SecurePreferences.getLanguage()}_${System.currentTimeMillis()}"

    suspend fun createIncident(
        type: String,
        description: String,
        lat: Double,
        lng: Double,
        severity: Int
    ): IncidentResponse? = withContext(Dispatchers.IO) {
        try {
            val res = api.createIncident(IncidentRequest(
                type, description, lat, lng, severity, incidentIdempotencyKey
            ))
            if (res.isSuccessful) {
                res.body()
            } else {
                queueIncidentForSync(type, description, lat, lng, severity)
                null
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Create incident failed, queuing", e)
            queueIncidentForSync(type, description, lat, lng, severity)
            null
        }
    }

    private suspend fun queueIncidentForSync(
        type: String, description: String, lat: Double, lng: Double, severity: Int
    ) {
        val dao = db.pendingIncidentDao()
        val key = incidentIdempotencyKey
        val request = IncidentRequest(type, description, lat, lng, severity, key)
        val entity = PendingIncidentEntity(
            idempotencyKey = key,
            incidentJson = json.encodeToString(IncidentRequest.serializer(), request),
            createdAt = System.currentTimeMillis(),
            retryCount = 0,
            lastAttemptAt = System.currentTimeMillis()
        )
        dao.insert(entity)
        val workRequest = OneTimeWorkRequestBuilder<SyncWorker>().build()
        workManager.enqueue(workRequest)
    }

    suspend fun syncPendingIncidents() {
        val dao = db.pendingIncidentDao()
        val pending = dao.getAll()
        if (pending.isEmpty()) return

        val requests = pending.map { it.toIncidentRequest() }
        val syncRequest = SyncIncidentsRequest(incidents = requests)

        try {
            val res = api.syncIncidents(syncRequest)
            if (res.isSuccessful) {
                val syncResponse = res.body() ?: return
                syncResponse.synced.forEach { synced ->
                    dao.deleteByIdempotencyKey(synced.idempotency_key)
                }
                syncResponse.failed.forEach { failed ->
                    dao.incrementRetryCount(failed.idempotency_key, System.currentTimeMillis())
                }
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Sync failed", e)
        }
    }

    // ============================================================
    // Incident tracking
    // ============================================================

    suspend fun getIncident(incidentId: String): IncidentDetail = withContext(Dispatchers.IO) {
        try {
            val res = api.getIncident(incidentId)
            if (res.isSuccessful) res.body() ?: fallbackIncident(incidentId)
            else {
                val entity = db.pendingIncidentDao().getByIdempotencyKey(incidentId)
                if (entity != null) {
                    val req = json.decodeFromString(IncidentRequest.serializer(), entity.incidentJson)
                    IncidentDetail(
                        id = incidentId, type = req.type, description = req.description,
                        lat = req.lat, lng = req.lng, severity = req.severity,
                        status = "OFFLINE_QUEUED", created_at = "", updated_at = "",
                        citizen_id = ""
                    )
                } else fallbackIncident(incidentId)
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Get incident failed", e)
            fallbackIncident(incidentId)
        }
    }

    private fun fallbackIncident(incidentId: String) = IncidentDetail(
        id = incidentId, type = "OTHER", description = "", lat = 0.0, lng = 0.0,
        severity = 0, status = "UNKNOWN", created_at = "", updated_at = "", citizen_id = ""
    )

    // ============================================================
    // Notifications / WebSocket
    // ============================================================

    suspend fun getNotifications(since: String? = null): List<Notification> = withContext(Dispatchers.IO) {
        try {
            val res = api.getNotifications(since)
            if (res.isSuccessful) res.body().orEmpty() else emptyList()
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Notifications unavailable", e)
            emptyList()
        }
    }

    // ============================================================
    // Location
    // ============================================================

    suspend fun getCurrentLocation(): LocationData = withContext(Dispatchers.IO) {
        try {
            val loc = suspendCancellableCoroutine<Location?> { cont ->
                val cts = CancellationTokenSource()
                cont.invokeOnCancellation { cts.cancel() }
                locationClient.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, cts.token)
                    .addOnSuccessListener { l -> if (cont.isActive) cont.resume(l) }
                    .addOnFailureListener { if (cont.isActive) cont.resumeWithException(it) }
            }
            LocationData(
                latitude = loc?.latitude, longitude = loc?.longitude,
                accuracy = loc?.accuracy?.toDouble(),
                status = "LOCATION_DETECTED", timestamp = System.currentTimeMillis()
            )
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Location unavailable, using fallback", e)
            LocationData(
                latitude = null, longitude = null,
                status = "LOCATION_UNAVAILABLE", isFallbackLocation = true
            )
        }
    }

    fun resetAuth() {
        SecurePreferences.setToken(null)
        CoroutineScope(Dispatchers.IO).launch { syncPendingIncidents() }
    }

    fun stopWebSocket() {
        ws.disconnect()
    }
}
