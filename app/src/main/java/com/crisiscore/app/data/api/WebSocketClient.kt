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
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

sealed class WsEvent {
    data class NotificationEvent(val notification: Notification) : WsEvent()
    data class IncidentUpdateEvent(
        val incidentId: String,
        val status: String,
        val volunteerName: String? = null,
        val volunteerPhone: String? = null,
        val etaMinutes: Int? = null
    ) : WsEvent()
    data object IncidentsChanged : WsEvent()
    data class Connected(val timestamp: Long = System.currentTimeMillis()) : WsEvent()
    data class Disconnected(val code: Int, val reason: String) : WsEvent()
}

class WebSocketClient(private val context: Context) {
    private var webSocket: WebSocket? = null
    private var job: Job? = null
    private val reconnectDelayMs = 5000L
    private val maxReconnectDelayMs = 60000L
    private var currentReconnectDelayMs = reconnectDelayMs

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }
    private var messageHandler: ((String) -> Unit)? = null

    private val _events = kotlinx.coroutines.flow.MutableSharedFlow<WsEvent>(
        replay = 1,
        extraBufferCapacity = 64,
        onBufferOverflow = kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST
    )
    val events: kotlinx.coroutines.flow.SharedFlow<WsEvent> = _events

    fun setMessageHandler(handler: (String) -> Unit) {
        messageHandler = handler
    }

    fun connect() {
        val token = SecurePreferences.getToken() ?: return

        val wsUrl = if (BuildConfig.WS_BASE_URL.contains("?")) {
            "${BuildConfig.WS_BASE_URL}&token=$token"
        } else {
            "${BuildConfig.WS_BASE_URL}?token=$token"
        }

        val request = Request.Builder()
            .url(wsUrl)
            .addHeader("Authorization", "Bearer $token")
            .build()

        val client = RetrofitClient.getOkHttpClient().newBuilder()
            .pingInterval(20, TimeUnit.SECONDS)
            .build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: okhttp3.Response) {
                Log.d("WebSocketClient", "Connected to Render WS")
                currentReconnectDelayMs = reconnectDelayMs
                _events.tryEmit(WsEvent.Connected())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    messageHandler?.invoke(text)
                    val map = json.decodeFromString<Map<String, kotlinx.serialization.json.JsonElement>>(text)

                    // Check for backend audit events: {"event":"audit","action":"verify","entity_type":"Incident",...}
                    val eventName = map["event"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                    val entityType = map["entity_type"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""

                    if (eventName == "audit" && entityType.equals("Incident", ignoreCase = true)) {
                        val incidentId = map["entity_id"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                        val action = map["action"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: "updated"
                        val afterObj = map["after"] as? kotlinx.serialization.json.JsonObject
                        val status = afterObj?.get("status")?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: action

                        Log.d("WebSocketClient", "Received Swagger incident audit: id=$incidentId action=$action status=$status")
                        _events.tryEmit(WsEvent.IncidentUpdateEvent(incidentId, status))
                        _events.tryEmit(WsEvent.IncidentsChanged)
                        return
                    }

                    val type = map["type"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                    when (type) {
                        "notification" -> {
                            val payload = map["payload"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: ""
                            val notif = json.decodeFromString<Notification>(payload)
                            Log.d("WebSocketClient", "Received notification: ${notif.title}")
                            _events.tryEmit(WsEvent.NotificationEvent(notif))
                        }
                        "incident_update" -> {
                            val incidentId = map["incidentId"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: "unknown"
                            val status = map["status"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null } ?: "UPDATED"
                            val volName = map["volunteerName"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null }
                            val volPhone = map["volunteerPhone"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content else null }
                            val eta = map["etaMinutes"]?.let { if (it is kotlinx.serialization.json.JsonPrimitive) it.content.toIntOrNull() else null }
                            Log.d("WebSocketClient", "Received incident update: $incidentId, status: $status")
                            _events.tryEmit(WsEvent.IncidentUpdateEvent(incidentId, status, volName, volPhone, eta))
                            _events.tryEmit(WsEvent.IncidentsChanged)
                        }
                        else -> Log.d("WebSocketClient", "Unhandled WS message: $text")
                    }
                } catch (e: Exception) {
                    Log.e("WebSocketClient", "Failed to parse message", e)
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                Log.d("WebSocketClient", "Closing: $code $reason")
                _events.tryEmit(WsEvent.Disconnected(code, reason))
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d("WebSocketClient", "Closed: $code $reason")
                _events.tryEmit(WsEvent.Disconnected(code, reason))
                scheduleReconnect()
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: okhttp3.Response?) {
                Log.e("WebSocketClient", "Error", t)
                _events.tryEmit(WsEvent.Disconnected(-1, t.message ?: "Failure"))
                scheduleReconnect()
            }
        })
    }

    private fun scheduleReconnect() {
        job?.cancel()
        job = CoroutineScope(Dispatchers.IO).launch {
            delay(currentReconnectDelayMs)
            currentReconnectDelayMs = (currentReconnectDelayMs * 2).coerceAtMost(maxReconnectDelayMs)
            if (isActive) {
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
