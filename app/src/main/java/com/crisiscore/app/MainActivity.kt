package com.crisiscore.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.crisiscore.app.ui.navigation.CrisisCoreNavHost
import com.crisiscore.app.ui.theme.CrisisCoreTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            CrisisCoreTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    CrisisCoreNavHost()
                }
            }
        }
    }
}
