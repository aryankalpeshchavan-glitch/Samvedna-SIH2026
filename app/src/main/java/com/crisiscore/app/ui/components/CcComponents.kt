package com.crisiscore.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
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
    val containerColor = when (variant) {
        CcButtonVariant.Emergency -> EmergencyRed
        CcButtonVariant.Warning -> WarningAmber
        CcButtonVariant.Secondary -> PrimaryGreen
        CcButtonVariant.Outline -> Color.Transparent
        CcButtonVariant.Ghost -> Color.Transparent
    }
    val contentColor = when (variant) {
        CcButtonVariant.Ghost -> TextSecondaryLight
        CcButtonVariant.Outline -> TextPrimaryLight
        else -> CanvasLight
    }
    val border: BorderStroke? = when (variant) {
        CcButtonVariant.Outline -> ButtonDefaults.outlinedButtonBorder(enabled)
        else -> null
    }

    Button(
        onClick = onClick,
        modifier = modifier.height(52.dp),
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(
            containerColor = containerColor,
            contentColor = contentColor,
            disabledContainerColor = containerColor.copy(alpha = 0.5f),
            disabledContentColor = contentColor.copy(alpha = 0.5f)
        ),
        shape = RoundedCornerShape(14.dp),
        contentPadding = PaddingValues(horizontal = 20.dp),
        border = border
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
        }
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
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = backgroundColor),
        border = BorderStroke(1.dp, borderColor),
    ) {
        Column(modifier = Modifier.padding(16.dp), content = content)
    }
}

@Composable
fun SeverityBadge(level: String, modifier: Modifier = Modifier) {
    val (color) = when (level.uppercase()) {
        "CRITICAL" -> Pair(BadgeCritical, Color.White)
        "HIGH" -> Pair(BadgeHigh, Color.White)
        "WATCH", "MEDIUM" -> Pair(BadgeWatch, Color.White)
        else -> Pair(BadgeLow, Color.White)
    }
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(color.copy(alpha = 0.15f))
            .padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(color)
        )
        Spacer(Modifier.width(6.dp))
        Text(
            text = level.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = color,
            fontWeight = FontWeight.Black
        )
    }
}

@Composable
fun DataSourceBadge(type: String = "live", modifier: Modifier = Modifier) {
    val (label, color) = when (type.lowercase()) {
        "live" -> "LIVE GIS" to PrimaryGreen
        "replayed" -> "REPLAYED FEED" to TextSecondaryLight
        "offline", "queued", "offline_queued" -> "OFFLINE QUEUED" to WarningAmber
        "stale" -> "STALE" to WarningAmber
        "unavailable" -> "UNAVAILABLE" to EmergencyRed
        else -> "LIVE GIS" to PrimaryGreen
    }
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(6.dp))
            .background(color.copy(alpha = 0.1f))
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
fun SectionHeader(
    title: String,
    modifier: Modifier = Modifier,
    trailing: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondaryLight
        )
        trailing?.invoke()
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
