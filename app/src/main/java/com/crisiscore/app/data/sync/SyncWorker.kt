package com.crisiscore.app.data.sync

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.local.OfflineDatabase
import com.crisiscore.app.data.model.SyncIncidentsRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class SyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        if (!isNetworkAvailable()) {
            return@withContext Result.retry()
        }

        val db = OfflineDatabase.getInstance(applicationContext)
        val dao = db.pendingIncidentDao()
        val pending = dao.getAll()

        if (pending.isEmpty()) {
            return@withContext Result.success()
        }

        val api = RetrofitClient.getApi()
        val requests = pending.map { it.toIncidentRequest() }
        val syncRequest = SyncIncidentsRequest(incidents = requests)

        try {
            val response = api.syncIncidents(syncRequest)
            if (response.isSuccessful) {
                val syncResponse = response.body() ?: return@withContext Result.retry()

                syncResponse.synced.forEach { synced ->
                    dao.deleteByIdempotencyKey(synced.idempotency_key)
                }

                syncResponse.failed.forEach { failed ->
                    dao.incrementRetryCount(failed.idempotency_key, System.currentTimeMillis())
                }
            }

            val remaining = dao.getAll()
            val hasRetriable = remaining.any { it.retryCount < 5 }
            return@withContext if (hasRetriable) Result.retry() else Result.success()
        } catch (e: Exception) {
            Log.e("SyncWorker", "Sync error", e)
            return@withContext Result.retry()
        }
    }

    private fun isNetworkAvailable(): Boolean {
        val cm = applicationContext.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = cm.activeNetwork ?: return false
        val capabilities = cm.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }
}
