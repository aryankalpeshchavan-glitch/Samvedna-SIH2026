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

    fun getUserPhone(): String? = getPrefs().getString("user_phone", null)

    fun setUserPhone(phone: String?) {
        getPrefs().edit().putString("user_phone", phone).apply()
    }

    fun getUserName(): String? = getPrefs().getString("user_name", null)

    fun setUserName(name: String?) {
        getPrefs().edit().putString("user_name", name).apply()
    }

    fun getUserRole(): String? = getPrefs().getString("user_role", null)

    fun setUserRole(role: String?) {
        getPrefs().edit().putString("user_role", role).apply()
    }

    fun isLoggedIn(): Boolean = !getToken().isNullOrBlank()

    fun clearAuth() {
        getPrefs().edit()
            .remove("auth_token")
            .remove("user_phone")
            .remove("user_name")
            .remove("user_role")
            .apply()
    }

    fun getLanguage(): String = getPrefs().getString("language", "en") ?: "en"

    fun setLanguage(code: String) {
        getPrefs().edit().putString("language", code).apply()
    }
}
