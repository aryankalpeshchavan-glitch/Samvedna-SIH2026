package com.crisiscore.app.data.api

import android.content.Context
import com.crisiscore.app.BuildConfig
import com.crisiscore.app.data.local.SecurePreferences
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    private var api: CrisisCoreApi? = null
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .addInterceptor { chain ->
            val original = chain.request()
            val builder = original.newBuilder()
            SecurePreferences.getToken()?.let { builder.header("Authorization", "Bearer $it") }
            chain.proceed(builder.build())
        }
        .build()

    fun initialize(context: Context) {
        SecurePreferences.init(context)

        api = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL.trimEnd('/') + "/")
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(CrisisCoreApi::class.java)
    }

    fun getApi(): CrisisCoreApi {
        return api ?: throw IllegalStateException("RetrofitClient not initialized. Ensure RetrofitClient.initialize(context) was called in Application.onCreate().")
    }

    fun getOkHttpClient(): OkHttpClient = client

    fun getBaseUrl(): String = BuildConfig.API_BASE_URL
    fun getWsUrl(): String = BuildConfig.WS_BASE_URL
}
