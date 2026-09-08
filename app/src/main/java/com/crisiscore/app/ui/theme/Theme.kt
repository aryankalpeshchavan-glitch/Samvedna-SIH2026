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

private val DarkColorScheme = androidx.compose.material3.darkColorScheme(
    primary = PrimaryGreenLight,
    onPrimary = CanvasDark,
    primaryContainer = PrimaryGreenDark,
    onPrimaryContainer = CanvasLight,
    secondary = WarningAmber,
    onSecondary = CanvasDark,
    secondaryContainer = WarningAmberDark.copy(alpha = 0.2f),
    onSecondaryContainer = CanvasLight,
    tertiary = EmergencyRed,
    onTertiary = CanvasLight,
    background = CanvasDark,
    onBackground = TextPrimaryDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark,
    surfaceVariant = SurfaceElevatedDark,
    surfaceContainerLow = CanvasDark,
    surfaceContainer = SurfaceDark,
    surfaceContainerHigh = BorderDark.copy(alpha = 0.4f),
    onSurfaceVariant = TextSecondaryDark,
    outline = BorderDark,
    error = EmergencyRed,
    onError = CanvasLight,
)

@Composable
fun CrisisCoreTheme(
    darkTheme: Boolean = androidx.compose.foundation.isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            window.navigationBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
