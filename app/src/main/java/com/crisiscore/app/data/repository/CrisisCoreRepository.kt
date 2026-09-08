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

    suspend fun createIncident(
        type: String,
        description: String,
        lat: Double,
        lng: Double,
        severity: Int
    ): IncidentResponse? = withContext(Dispatchers.IO) {
        val key = java.util.UUID.randomUUID().toString()
        try {
            val res = api.createIncident(IncidentRequest(
                type, description, lat, lng, severity, key
            ))
            if (res.isSuccessful && res.body() != null) {
                res.body()
            } else {
                queueIncidentForSync(key, type, description, lat, lng, severity)
                IncidentResponse(id = key, status = "QUEUED_OFFLINE")
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreRepo", "Create incident failed, queuing", e)
            queueIncidentForSync(key, type, description, lat, lng, severity)
            IncidentResponse(id = key, status = "QUEUED_OFFLINE")
        }
    }

    private suspend fun queueIncidentForSync(
        key: String, type: String, description: String, lat: Double, lng: Double, severity: Int
    ) {
        val dao = db.pendingIncidentDao()
        val request = IncidentRequest(type, description, lat, lng, severity, key)
        val entity = PendingIncidentEntity(
            idempotencyKey = key,
            incidentJson = json.encodeToString(IncidentRequest.serializer(), request),
            createdAt = System.currentTimeMillis(),
            retryCount = 0,
            lastAttemptAt = System.currentTimeMillis()
        )
        dao.insert(entity)
        val constraints = androidx.work.Constraints.Builder()
            .setRequiredNetworkType(androidx.work.NetworkType.CONNECTED)
            .build()
        val workRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .setBackoffCriteria(androidx.work.BackoffPolicy.EXPONENTIAL, 10, java.util.concurrent.TimeUnit.MINUTES)
            .build()
        workManager.enqueueUniqueWork("incident_sync", androidx.work.ExistingWorkPolicy.KEEP, workRequest)
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

    // ============================================================
    // Family Members Persistence
    // ============================================================

    fun getFamilyMembersFlow(): kotlinx.coroutines.flow.Flow<List<FamilyMember>> {
        return db.familyMemberDao().getAllFlow().let { flow ->
            kotlinx.coroutines.flow.flow {
                flow.collect { entities ->
                    emit(entities.map { it.toFamilyMember() })
                }
            }
        }
    }

    suspend fun getAllFamilyMembers(): List<FamilyMember> = withContext(Dispatchers.IO) {
        db.familyMemberDao().getAll().map { it.toFamilyMember() }
    }

    suspend fun addFamilyMember(member: FamilyMember) = withContext(Dispatchers.IO) {
        db.familyMemberDao().insert(com.crisiscore.app.data.local.FamilyMemberEntity.fromFamilyMember(member))
    }

    suspend fun updateFamilyMemberStatus(id: String, status: FamilyMemberStatus, checkedInBy: String?, checkedInAt: String?) = withContext(Dispatchers.IO) {
        db.familyMemberDao().updateStatus(id, status.name, checkedInBy, checkedInAt)
    }

    suspend fun deleteFamilyMember(id: String) = withContext(Dispatchers.IO) {
        db.familyMemberDao().deleteById(id)
    }

    // ============================================================
    // WebSocket
    // ============================================================

    fun getWebSocketEvents(): kotlinx.coroutines.flow.SharedFlow<com.crisiscore.app.data.api.WsEvent> = ws.events

    fun reconnectWebSocket() {
        ws.connect()
    }

    fun resetAuth() {
        SecurePreferences.setToken(null)
        CoroutineScope(Dispatchers.IO).launch { syncPendingIncidents() }
    }

    fun stopWebSocket() {
        ws.disconnect()
    }
}
