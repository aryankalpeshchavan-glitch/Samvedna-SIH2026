package com.crisiscore.app.ui.components

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Emergency
import androidx.compose.material3.Icon
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.foundation.layout.RowScope
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.animation.core.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import kotlin.math.roundToInt

@Composable
fun ClaySurface(
    color: Color,
    modifier: Modifier = Modifier,
    shape: RoundedCornerShape = ClayShapes.card,
    depth: Dp = 8.dp,
    tint: Color? = null,
    contentColor: Color = Color.Unspecified,
    enabled: Boolean = true,
    onClick: (() -> Unit)? = null,
    content: @Composable () -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by if (onClick != null) interactionSource.collectIsPressedAsState() else remember { mutableStateOf(false) }

    val animatedElevation by animateDpAsState(
        targetValue = if (isPressed) depth * 0.3f else depth,
        animationSpec = tween(durationMillis = 120),
        label = "clayElevation"
    )
    val animatedScale by animateFloatAsState(
        targetValue = if (isPressed) 0.97f else 1f,
        animationSpec = tween(durationMillis = 120),
        label = "clayScale"
    )

    val topColor = lerpColor(color, Color.White, if (isPressed) 0.02f else 0.14f)
    val bottomColor = lerpColor(color, Color.Black, if (isPressed) 0.10f else 0.04f)

    val base = Modifier
        .graphicsLayer {
            scaleX = animatedScale
            scaleY = animatedScale
        }
        .shadow(animatedElevation, shape, clip = false, ambientColor = ClayShadow, spotColor = ClayShadow)
        .clip(shape)
        .background(
            Brush.verticalGradient(
                colors = listOf(topColor, color, bottomColor),
                startY = 0f,
                endY = Float.POSITIVE_INFINITY
            )
        )
        .then(
            if (tint != null) Modifier.border(BorderStroke(1.dp, tint.copy(alpha = 0.5f)), shape) else Modifier
        )
        .then(
            if (onClick != null) {
                Modifier.clickable(
                    interactionSource = interactionSource,
                    indication = null,
                    enabled = enabled,
                    onClick = onClick
                )
            } else Modifier
        )

    val resolvedContent = LocalContentColor.current
    Box(modifier = modifier.then(base)) {
        CompositionLocalProvider(LocalContentColor provides (if (contentColor == Color.Unspecified) resolvedContent else contentColor)) {
            content()
        }
    }
}

@Composable
fun ClayButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    color: Color = PrimaryGreen,
    contentColor: Color = CanvasLight,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    shape: RoundedCornerShape = ClayShapes.pill,
    height: Dp = 56.dp,
    content: @Composable RowScope.() -> Unit
) {
    ClaySurface(
        color = color,
        modifier = modifier.height(height),
        shape = shape,
        depth = 10.dp,
        contentColor = contentColor,
        enabled = enabled,
        onClick = onClick
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 22.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (icon != null) {
                Icon(imageVector = icon, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
            }
            content()
        }
    }
}

@Composable
fun ClayTextButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    color: Color = PrimaryGreen,
    content: @Composable RowScope.() -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isPressed by interactionSource.collectIsPressedAsState()
    val alpha by animateFloatAsState(
        targetValue = if (isPressed) 0.5f else 1f,
        animationSpec = tween(durationMillis = 100),
        label = "textBtnAlpha"
    )
    Row(
        modifier = modifier
            .graphicsLayer { this.alpha = alpha }
            .clickable(
                interactionSource = interactionSource,
                indication = null,
                enabled = enabled,
                onClick = onClick
            )
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        CompositionLocalProvider(LocalContentColor provides color) {
            content()
        }
    }
}

@Composable
fun EmergencySosButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    haptic: () -> Unit = {}
) {
    val pulse = rememberInfiniteTransition(label = "sosPulse")
    val scale by pulse.animateFloat(
        initialValue = 1f,
        targetValue = 1.015f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "sosScale"
    )

    ClaySurface(
        color = EmergencyRed,
        modifier = modifier
            .fillMaxWidth()
            .height(62.dp)
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
            },
        shape = ClayShapes.pill,
        depth = 12.dp,
        contentColor = CanvasLight,
        onClick = {
            haptic()
            onClick()
        }
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 22.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(imageVector = Icons.Filled.Emergency, contentDescription = null, modifier = Modifier.size(28.dp))
            Spacer(Modifier.width(14.dp))
            Column {
                Text(
                    T("home.triggerSos"),
                    color = CanvasLight,
                    fontWeight = FontWeight.Black,
                    fontSize = 15.sp,
                    letterSpacing = 1.4.sp
                )
                Text(
                    T("home.sosDescription"),
                    color = CanvasLight.copy(alpha = 0.78f),
                    fontSize = 10.sp,
                    letterSpacing = 0.7.sp
                )
            }
        }
    }
}

@Composable
fun ClayChip(
    label: String,
    color: Color,
    modifier: Modifier = Modifier,
    dot: Boolean = true
) {
    ClaySurface(
        color = color.copy(alpha = 0.12f),
        modifier = modifier,
        shape = ClayShapes.chip,
        depth = 0.dp,
        tint = color.copy(alpha = 0.35f),
        contentColor = color
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            if (dot) {
                Box(
                    modifier = Modifier
                        .size(7.dp)
                        .clip(CircleShape)
                        .background(color)
                )
                Spacer(Modifier.width(6.dp))
            }
            Text(
                label,
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, letterSpacing = 0.8.sp),
                fontWeight = FontWeight.Bold,
                maxLines = 1
            )
        }
    }
}

private fun lerpColor(a: Color, b: Color, t: Float): Color = Color(
    red = a.red + (b.red - a.red) * t,
    green = a.green + (b.green - a.green) * t,
    blue = a.blue + (b.blue - a.blue) * t,
    alpha = a.alpha + (b.alpha - a.alpha) * t
)

internal fun riskLevelColor(level: String): Color = when (level.uppercase()) {
    "CRITICAL" -> RiskCritical
    "HIGH" -> RiskHigh
    "MEDIUM", "WATCH" -> RiskModerate
    "LOW" -> RiskLow
    else -> RiskUnknown
}

internal fun riskLevelRank(level: String): Int = when (level.uppercase()) {
    "CRITICAL" -> 5
    "HIGH" -> 4
    "MEDIUM" -> 3
    "WATCH" -> 2
    "LOW" -> 1
    else -> 0
}

internal fun riskScoreText(score: Double): String = "Risk score ${score.roundToInt()}/100"
