package com.crisiscore.app.data.repository

import android.content.Context
import android.location.Location
import android.util.Log
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.model.*
import com.crisiscore.app.data.local.SecurePreferences
import com.crisiscore.app.data.local.SyntheticRiskData
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

class CrisisCoreRepository(private val context: Context) {
    private val api = RetrofitClient.getApi()
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

    suspend fun getRiskZones(): List<RiskZone> = withContext(Dispatchers.IO) {
        try {
            val res = api.getRisk()
            val live = if (res.isSuccessful) res.body().orEmpty() else emptyList()
            if (live.isNotEmpty()) live else SyntheticRiskData.zones()
        } catch (e: Exception) {
            Log.w("CrisisCoreRepo", "Risk feed unavailable, using synthetic", e)
            SyntheticRiskData.zones()
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
}
