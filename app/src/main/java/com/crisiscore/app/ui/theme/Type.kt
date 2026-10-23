package com.crisiscore.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.sp

// High-performance, glitch-free typography using system sans-serif and monospace
val SansFontFamily = FontFamily.SansSerif
val MonoFontFamily = FontFamily.Monospace

private val defaultPlatformStyle = PlatformTextStyle(
    includeFontPadding = false
)

private val defaultLineHeightStyle = LineHeightStyle(
    alignment = LineHeightStyle.Alignment.Center,
    trim = LineHeightStyle.Trim.None
)

val Typography = Typography(
    displayLarge = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Black,
        fontSize = 32.sp,
        lineHeight = 38.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    headlineLarge = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 24.sp,
        lineHeight = 30.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    headlineMedium = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 20.sp,
        lineHeight = 26.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    titleLarge = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 18.sp,
        lineHeight = 24.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    titleMedium = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.SemiBold,
        fontSize = 15.sp,
        lineHeight = 21.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    bodyLarge = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    bodyMedium = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    bodySmall = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 17.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    labelLarge = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.1.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    labelMedium = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    ),
    labelSmall = TextStyle(
        fontFamily = SansFontFamily,
        fontWeight = FontWeight.SemiBold,
        fontSize = 10.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.3.sp,
        platformStyle = defaultPlatformStyle,
        lineHeightStyle = defaultLineHeightStyle
    )
)