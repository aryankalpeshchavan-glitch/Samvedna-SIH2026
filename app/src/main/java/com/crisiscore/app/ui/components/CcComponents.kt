package com.crisiscore.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.foundation.layout.RowScope
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.ui.theme.*

enum class CcButtonVariant { Emergency, Warning, Secondary, Outline, Ghost }

@Composable
fun CcButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    variant: CcButtonVariant = CcButtonVariant.Secondary,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    content: @Composable RowScope.() -> Unit
) {
    val (color, contentColor) = when (variant) {
        CcButtonVariant.Emergency -> EmergencyRed to CanvasLight
        CcButtonVariant.Warning -> WarningAmber to CanvasLight
        CcButtonVariant.Secondary -> PrimaryGreen to CanvasLight
        CcButtonVariant.Outline -> CanvasLight to TextPrimaryLight
        CcButtonVariant.Ghost -> Color.Transparent to TextSecondaryLight
    }

    if (variant == CcButtonVariant.Ghost) {
        ClayTextButton(onClick = onClick, modifier = modifier, enabled = enabled, color = contentColor) {
            if (icon != null) {
                Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
            }
            content()
        }
        return
    }

    ClayButton(
        onClick = onClick,
        modifier = modifier,
        color = color,
        contentColor = contentColor,
        enabled = enabled,
        icon = icon,
        shape = ClayShapes.button,
        height = 54.dp
    ) {
        content()
    }
}

@Composable
fun CcCard(
    modifier: Modifier = Modifier,
    borderColor: Color = BorderLight,
    backgroundColor: Color = SurfaceLight,
    content: @Composable ColumnScope.() -> Unit
) {
    ClaySurface(
        color = if (backgroundColor == SurfaceLight) ClayCreamTint else backgroundColor,
        modifier = modifier,
        shape = ClayShapes.card,
        depth = 8.dp,
        tint = borderColor
    ) {
        Column(modifier = Modifier.padding(start = 18.dp, end = 18.dp, top = 16.dp, bottom = 16.dp), content = content)
    }
}

@Composable
fun SeverityBadge(level: String, modifier: Modifier = Modifier) {
    val color = riskLevelColor(level)
    ClayChip(
        label = level.uppercase(),
        color = color,
        modifier = modifier
    )
}

@Composable
fun DataSourceBadge(type: String = "synthetic", modifier: Modifier = Modifier) {
    val (label, color) = when (type) {
        "live" -> "LIVE GIS" to PrimaryGreen
        "replayed" -> "REPLAYED FEED" to TextSecondaryLight
        "synthetic" -> "SYNTHETIC DEMO" to WarningAmber
        else -> "DEMO DATA" to TextSecondaryLight
    }
    Row(
        modifier = modifier
            .clip(ClayShapes.chip)
            .background(color.copy(alpha = 0.12f))
            .padding(horizontal = 8.dp, vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, letterSpacing = 1.sp),
            color = color,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun PageHeader(
    tag: String,
    title: String,
    modifier: Modifier = Modifier,
    trailing: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Bottom
    ) {
        Column {
            Text(
                text = tag,
                style = MaterialTheme.typography.labelSmall.copy(
                    letterSpacing = 2.sp,
                    color = PrimaryGreen
                )
            )
            Text(
                text = title,
                style = MaterialTheme.typography.headlineMedium
            )
        }
        trailing?.invoke()
    }
}
