package com.crisiscore.app

import android.app.Application
import android.util.Log
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.local.CrisisCoreDatabase
import com.crisiscore.app.data.repository.CrisisCoreRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import org.maplibre.android.MapLibre

class CrisisCoreApp : Application() {
    val database: CrisisCoreDatabase by lazy {
        CrisisCoreDatabase.getInstance(this)
    }

    override fun onCreate() {
        super.onCreate()
        try {
            RetrofitClient.initialize(this)
            kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                com.crisiscore.app.data.repository.CrisisCoreRepository(this@CrisisCoreApp).ensureAuthenticated()
            }
        } catch (e: Exception) {
            Log.e("CrisisCoreApp", "RetrofitClient init failed", e)
        }
        try {
            MapLibre.getInstance(this)
        } catch (e: Exception) {
            Log.e("CrisisCoreApp", "MapLibre init failed", e)
        }
    }
}
