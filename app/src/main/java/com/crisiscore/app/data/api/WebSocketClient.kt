package com.crisiscore.app.data.api

import android.content.Context
import android.util.Log
import com.crisiscore.app.BuildConfig
import com.crisiscore.app.data.local.SecurePreferences
import com.crisiscore.app.data.model.Notification
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

class WebSocketClient(private val context: Context) {
    private var webSocket: WebSocket? = null
    private var job: Job? = null
    private val reconnectDelayMs = 5000L
    private val maxReconnectDelayMs = 60000L
    private var currentReconnectDelayMs = reconnectDelayMs

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private var messageHandler: ((String) -> Unit)? = null

    fun setMessageHandler(handler: (String) -> Unit) {
        messageHandler = handler
    }

    fun connect() {
        val token = SecurePreferences.getToken() ?: return

        val request = Request.Builder()
            .url(BuildConfig.WS_BASE_URL)
            .addHeader("Authorization", "Bearer $token")
            .build()

        val client = OkHttpClient.Builder()
            .pingInterval(20, TimeUnit.SECONDS)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: okhttp3.Response) {
                Log.d("WebSocketClient", "Connected")
                currentReconnectDelayMs = reconnectDelayMs
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val map = json.decodeFromString<Map<String, kotlinx.serialization.json.JsonElement>>(text)
                    val type = map["type"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                    when (type) {
                        "notification" -> {
                            val payload = map["payload"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                            val notif = json.decodeFromString<Notification>(payload)
                            Log.d("WebSocketClient", "Received notification: ${notif.title}")
                        }
                        "incident_update" -> {
                            val incidentId = map["incidentId"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: "unknown"
                            Log.d("WebSocketClient", "Received incident update: $incidentId")
                        }
                        else -> Log.d("WebSocketClient", "Unknown message type: $type")
                    }
                } catch (e: Exception) {
                    Log.e("WebSocketClient", "Failed to parse message", e)
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                Log.d("WebSocketClient", "Closing: $code $reason")
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d("WebSocketClient", "Closed: $code $reason")
                scheduleReconnect()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                Log.e("WebSocketClient", "Error", t)
                scheduleReconnect()
            }
        })
    }

    private fun scheduleReconnect() {
        job?.cancel()
        job = CoroutineScope(Dispatchers.IO).launch {
            delay(currentReconnectDelayMs)
            currentReconnectDelayMs = (currentReconnectDelayMs * 2).coerceAtMost(maxReconnectDelayMs)
            if (!Thread.currentThread().isInterrupted) {
                connect()
            }
        }
    }

    fun sendPing() {
        webSocket?.send("""{"type": "ping"}""")
    }

    fun disconnect() {
        job?.cancel()
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
        currentReconnectDelayMs = reconnectDelayMs
    }
}
