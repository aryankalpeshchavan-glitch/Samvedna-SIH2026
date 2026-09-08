package com.crisiscore.app

import android.app.Application
import android.util.Log
import com.crisiscore.app.data.api.RetrofitClient
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.util.LocaleManager
import com.crisiscore.app.util.TtsManager
import org.maplibre.android.MapLibre

class CrisisCoreApp : Application() {

    lateinit var repository: CrisisCoreRepository
        private set

    override fun onCreate() {
        super.onCreate()
        try {
            RetrofitClient.initialize(this)
            LocaleManager.init()
            TtsManager.init(this)
        } catch (e: Exception) {
            Log.e("CrisisCoreApp", "RetrofitClient/LocaleManager/TtsManager init failed", e)
        }
        try {
            repository = CrisisCoreRepository(this)
        } catch (e: Exception) {
            Log.e("CrisisCoreApp", "CrisisCoreRepository init failed", e)
        }
        try {
            MapLibre.getInstance(this)
        } catch (e: Exception) {
            Log.e("CrisisCoreApp", "MapLibre init failed", e)
        }
    }
}