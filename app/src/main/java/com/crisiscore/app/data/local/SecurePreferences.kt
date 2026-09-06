package com.crisiscore.app.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

object SecurePreferences {
    private const val PREFS_NAME = "crisiscore_secure_prefs"

    private var prefs: SharedPreferences? = null

    fun init(context: Context) {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        prefs = EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    fun getPrefs(): SharedPreferences {
        return prefs ?: throw IllegalStateException("SecurePreferences not initialized. Call init(context) first.")
    }

    fun getToken(): String? = getPrefs().getString("auth_token", null)

    fun setToken(token: String?) {
        getPrefs().edit().putString("auth_token", token).apply()
    }

    fun getDemoPhone(): String? = getPrefs().getString("demo_phone", null)

    fun setDemoPhone(phone: String) {
        getPrefs().edit().putString("demo_phone", phone).apply()
    }

    fun getLanguage(): String = getPrefs().getString("language", "en") ?: "en"

    fun setLanguage(code: String) {
        getPrefs().edit().putString("language", code).apply()
    }
}
