package com.crisiscore.app.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = PrimaryGreen,
    onPrimary = CanvasLight,
    primaryContainer = PrimaryGreenLight,
    onPrimaryContainer = CanvasLight,
    secondary = WarningAmber,
    onSecondary = CanvasLight,
    secondaryContainer = WarningAmber.copy(alpha = 0.15f),
    onSecondaryContainer = CanvasLight,
    tertiary = EmergencyRed,
    onTertiary = CanvasLight,
    background = CanvasLight,
    onBackground = TextPrimaryLight,
    surface = SurfaceLight,
    onSurface = TextPrimaryLight,
    surfaceVariant = SurfaceLight,
    surfaceContainerLow = CanvasLight,
    surfaceContainer = SurfaceLight,
    surfaceContainerHigh = BorderLight.copy(alpha = 0.3f),
    onSurfaceVariant = TextSecondaryLight,
    outline = BorderLight,
    error = EmergencyRed,
    onError = CanvasLight,
)

@Composable
fun CrisisCoreTheme(
    content: @Composable () -> Unit
) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = CanvasLight.toArgb()
            window.navigationBarColor = CanvasLight.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = true
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = true
        }
    }

    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}
