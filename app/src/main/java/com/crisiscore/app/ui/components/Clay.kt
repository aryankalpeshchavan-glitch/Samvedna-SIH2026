package com.crisiscore.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.isSystemInDarkTheme
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
import androidx.compose.ui.composed
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
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

private fun lerpColor(a: Color, b: Color, t: Float): Color = Color(
    red = a.red + (b.red - a.red) * t,
    green = a.green + (b.green - a.green) * t,
    blue = a.blue + (b.blue - a.blue) * t,
    alpha = a.alpha + (b.alpha - a.alpha) * t
)

@Composable
private fun clayShadow(): Color = if (isSystemInDarkTheme()) ClayShadowNight else ClayShadow

@Composable
private fun clayHighlight(): Color = if (isSystemInDarkTheme()) Color.Transparent else ClayHighlight

@Composable
fun Modifier.clayBody(
    color: Color,
    shape: RoundedCornerShape,
    pressed: Boolean,
    depth: Dp,
    tint: Color? = null,
    shadow: Color,
    highlight: Color
): Modifier = composed {
    val elevation = if (pressed) depth * 0.28f else depth
    val top = lerpColor(color, Color.White, if (pressed) 0.015f else 0.16f)
    val bottom = lerpColor(color, Color.Black, if (pressed) 0.12f else 0.05f)
    this
        .graphicsLayer {
            translationY = if (pressed) depth.toPx() * 0.26f else 0f
            scaleX = if (pressed) 0.975f else 1f
            scaleY = if (pressed) 0.975f else 1f
        }
        .shadow(elevation, shape, clip = false, ambientColor = shadow, spotColor = shadow)
        .shadow(if (pressed) 0.dp else 2.dp, shape, clip = false, ambientColor = highlight, spotColor = highlight)
        .clip(shape)
        .background(
            Brush.linearGradient(
                colors = listOf(top, color, bottom),
                start = Offset.Zero,
                end = Offset.Infinite
            )
        )
        .then(
            if (tint != null) Modifier.border(BorderStroke(1.dp, tint.copy(alpha = 0.55f)), shape) else Modifier
        )
}

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
    val shadow = clayShadow()
    val highlight = clayHighlight()
    val interactionSource = remember { MutableInteractionSource() }
    val pressed by if (onClick != null) interactionSource.collectIsPressedAsState() else remember { mutableStateOf(false) }

    val base = Modifier
        .clayBody(color, shape, pressed, depth, tint, shadow, highlight)
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
        Box(
            modifier = Modifier
                .matchParentSize()
                .clip(shape)
                .background(
                    Brush.verticalGradient(
                        colors = listOf(Color.White.copy(alpha = 0.10f), Color.Transparent),
                        startY = 0f,
                        endY = 0.62f
                    )
                )
        )
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
    val pressed by interactionSource.collectIsPressedAsState()
    Row(
        modifier = modifier
            .graphicsLayer {
                alpha = if (pressed) 0.6f else 1f
            }
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
        targetValue = 1.018f,
        animationSpec = infiniteRepeatable(
            animation = tween(700, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "sosScale"
    )
    val alpha by pulse.animateFloat(
        initialValue = 0.92f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(700, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "sosAlpha"
    )

    ClaySurface(
        color = EmergencyRed,
        modifier = modifier
            .fillMaxWidth()
            .height(62.dp)
            .graphicsLayer {
                this.scaleX = scale
                this.scaleY = scale
                this.alpha = alpha
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