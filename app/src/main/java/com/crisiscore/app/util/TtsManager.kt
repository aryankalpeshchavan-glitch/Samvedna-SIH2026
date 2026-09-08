package com.crisiscore.app.util

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

object TtsManager : TextToSpeech.OnInitListener {
    private var tts: TextToSpeech? = null
    private var isInitialized = false

    fun init(context: Context) {
        if (tts == null) {
            tts = TextToSpeech(context.applicationContext, this)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isInitialized = true
            tts?.language = Locale("en", "IN")
        } else {
            Log.e("TtsManager", "TTS initialization failed with status: $status")
        }
    }

    fun speak(text: String, languageCode: String = "en") {
        if (!isInitialized || tts == null) return
        val locale = when (languageCode) {
            "hi" -> Locale("hi", "IN")
            "bn" -> Locale("bn", "IN")
            "as" -> Locale("as", "IN")
            else -> Locale("en", "IN")
        }
        val result = tts?.setLanguage(locale)
        if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
            tts?.language = Locale("en", "IN")
        }
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "crisiscore_tts_${System.currentTimeMillis()}")
    }

    fun stop() {
        tts?.stop()
    }
}
