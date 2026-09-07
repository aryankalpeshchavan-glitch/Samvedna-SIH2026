package com.crisiscore.app

import android.app.Application
import android.util.Log
import com.crisiscore.app.data.api.RetrofitClient
import org.maplibre.android.MapLibre

class CrisisCoreApp : Application() {
    override fun onCreate() {
        super.onCreate()
        try {
            RetrofitClient.initialize(this)
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