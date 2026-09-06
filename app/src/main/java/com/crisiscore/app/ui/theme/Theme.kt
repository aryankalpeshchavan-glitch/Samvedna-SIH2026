package com.crisiscore.app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
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

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryGreen,
    onPrimary = CanvasDark,
    primaryContainer = PrimaryGreenLight,
    onPrimaryContainer = CanvasDark,
    secondary = WarningAmber,
    onSecondary = CanvasDark,
    secondaryContainer = WarningAmber.copy(alpha = 0.15f),
    onSecondaryContainer = CanvasDark,
    tertiary = EmergencyRed,
    onTertiary = CanvasDark,
    background = CanvasDark,
    onBackground = TextPrimaryDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark,
    surfaceVariant = SurfaceElevatedDark,
    surfaceContainerLow = CanvasDark,
    surfaceContainer = SurfaceDark,
    surfaceContainerHigh = SurfaceElevatedDark,
    onSurfaceVariant = TextSecondaryDark,
    outline = BorderDark,
    error = EmergencyRed,
    onError = CanvasDark,
)

@Composable
fun CrisisCoreTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
