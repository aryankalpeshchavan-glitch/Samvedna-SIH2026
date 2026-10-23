package com.crisiscore.app.ui.components

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color as AColor
import android.graphics.Paint
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.*
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.crisiscore.app.data.model.IncidentOut
import com.crisiscore.app.data.model.LocationData
import com.crisiscore.app.data.model.RiskZone
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import org.maplibre.android.annotations.IconFactory
import org.maplibre.android.annotations.MarkerOptions
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.MapLibreMap

private const val CAMERA_ZOOM_REGION = 12.0
private const val CAMERA_ZOOM_STATE = 7.0

private fun buildRiskIcon(accent: Color): Bitmap {
    val size = 64
    val cx = size / 2f
    val cy = size / 2f
    val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
    val c = Canvas(bmp)
    val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = accent.toArgb() }
    val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 3.6f
        color = AColor.WHITE
    }
    val shadow = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = AColor.argb(80, 20, 20, 16) }
    val gloss = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = AColor.argb(70, 255, 255, 255) }

    c.drawCircle(cx, cy, 18f, shadow)
    c.drawCircle(cx, cy, 16f, fill)
    c.drawCircle(cx, cy, 13.4f, ring)
    c.drawCircle(cx - 5f, cy - 5f, 5.5f, gloss)
    return bmp
}

private fun buildIncidentIcon(severity: Int, status: String): Bitmap {
    val size = 72
    val cx = size / 2f
    val cy = size / 2f
    val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
    val c = Canvas(bmp)

    val baseColor = when (severity) {
        5 -> AColor.rgb(220, 38, 38)     // Red
        4 -> AColor.rgb(234, 88, 12)     // Orange-Red
        3 -> AColor.rgb(245, 158, 11)    // Amber
        2 -> AColor.rgb(202, 138, 4)     // Yellow-Gold
        else -> AColor.rgb(37, 99, 235)   // Blue
    }

    val isVerified = status.equals("verified", ignoreCase = true)
    val ringColor = if (isVerified) AColor.rgb(16, 185, 129) else AColor.WHITE

    val shadowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = AColor.argb(90, 0, 0, 0) }
    val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = baseColor }
    val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = if (isVerified) 4.5f else 3.2f
        color = ringColor
    }
    val innerDot = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = AColor.WHITE }

    c.drawCircle(cx, cy + 2f, 20f, shadowPaint)
    c.drawCircle(cx, cy, 18f, fillPaint)
    c.drawCircle(cx, cy, 18f, ringPaint)
    c.drawCircle(cx, cy, 6f, innerDot)

    if (isVerified) {
        val haloPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.2f
            color = AColor.argb(200, 16, 185, 129)
        }
        c.drawCircle(cx, cy, 23f, haloPaint)
    }

    return bmp
}

private fun Color.toArgb(): Int = AColor.rgb(
    (red * 255).toInt(),
    (green * 255).toInt(),
    (blue * 255).toInt()
)

@Composable
fun CrisisMapView(
    location: LocationData?,
    riskZones: List<RiskZone>,
    incidents: List<IncidentOut> = emptyList(),
    isEmergencyMode: Boolean,
    onMyLocationClick: () -> Unit,
    onEmergencyToggle: () -> Unit,
    onIncidentClick: ((IncidentOut) -> Unit)? = null,
    onRefreshIncidents: (() -> Unit)? = null,
    isRefreshing: Boolean = false,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var mapView by remember { mutableStateOf<MapView?>(null) }
    var mapboxMap by remember { mutableStateOf<MapLibreMap?>(null) }
    val iconCache = remember { mutableMapOf<String, org.maplibre.android.annotations.Icon>() }
    var selectedIncident by remember { mutableStateOf<IncidentOut?>(null) }
    var activeFilter by remember { mutableStateOf("ALL") } // "ALL", "VERIFIED", "REPORTED", "RISK"

    fun riskIconFor(level: String): org.maplibre.android.annotations.Icon {
        val key = "risk_${level.uppercase()}"
        return iconCache.getOrPut(key) {
            val bmp = buildRiskIcon(riskLevelColor(level.uppercase()))
            IconFactory.getInstance(context).fromBitmap(bmp)
        }
    }

    fun incidentIconFor(severity: Int, status: String): org.maplibre.android.annotations.Icon {
        val key = "inc_${severity}_${status.lowercase()}"
        return iconCache.getOrPut(key) {
            val bmp = buildIncidentIcon(severity, status)
            IconFactory.getInstance(context).fromBitmap(bmp)
        }
    }

    LaunchedEffect(Unit) {
        try {
            org.maplibre.android.MapLibre.getInstance(context)
        } catch (_: Exception) { }
    }

    // Camera animation on location change
    LaunchedEffect(location) {
        mapboxMap?.let { map ->
            if (location?.latitude != null && location.longitude != null) {
                val target = LatLng(location.latitude, location.longitude)
                map.animateCamera(CameraUpdateFactory.newLatLngZoom(target, CAMERA_ZOOM_REGION))
            }
        }
    }

    // Render Markers on MapLibre
    LaunchedEffect(location, riskZones, incidents, isEmergencyMode, activeFilter) {
        mapboxMap?.let { map ->
            map.clear()

            // 1. User Location Marker
            if (location?.latitude != null && location.longitude != null) {
                val latLng = LatLng(location.latitude, location.longitude)
                map.addMarker(
                    MarkerOptions()
                        .position(latLng)
                        .icon(riskIconFor("SAFE"))
                        .title(T.get("map.yourLocation"))
                        .snippet(T.get("map.gpsAccuracy").replace("{m}", "${location.accuracy?.toInt() ?: "?"}"))
                )
            }

            // 2. Incident Markers (from Swagger / Render Backend)
            if (activeFilter != "RISK") {
                val filteredIncidents = when (activeFilter) {
                    "VERIFIED" -> incidents.filter { it.status.equals("verified", ignoreCase = true) }
                    "REPORTED" -> incidents.filter { !it.status.equals("verified", ignoreCase = true) }
                    else -> incidents
                }

                filteredIncidents.forEach { inc ->
                    val latLng = LatLng(inc.lat, inc.lng)
                    val isVerified = inc.status.equals("verified", ignoreCase = true)
                    val statusBadge = if (isVerified) "[VERIFIED]" else "[${inc.status.uppercase()}]"
                    val typeText = inc.type.replace('_', ' ').uppercase()
                    val snippetText = inc.description?.ifBlank { "Reported incident" } ?: "Swagger incident"

                    map.addMarker(
                        MarkerOptions()
                            .position(latLng)
                            .icon(incidentIconFor(inc.severity, inc.status))
                            .title("$statusBadge $typeText (Level ${inc.severity})")
                            .snippet(snippetText)
                    )
                }
            }

            // 3. Risk Zone Markers
            if (activeFilter == "ALL" || activeFilter == "RISK") {
                riskZones.forEach { zone ->
                    val latLng = LatLng(zone.lat, zone.lng)
                    val level = zone.risk_level.ifBlank { "LOW" }.uppercase()
                    val title = zone.name ?: T.get("home.riskZone")
                    map.addMarker(
                        MarkerOptions()
                            .position(latLng)
                            .icon(riskIconFor(level))
                            .title("$title \u2014 $level")
                            .snippet(T.get("map.riskScore").replace("{n}", "${zone.risk_score.toInt()}"))
                    )
                }
            }

            // Listen to marker clicks
            map.setOnMarkerClickListener { marker ->
                val pos = marker.position
                val matching = incidents.find {
                    Math.abs(it.lat - pos.latitude) < 0.0002 && Math.abs(it.lng - pos.longitude) < 0.0002
                }
                if (matching != null) {
                    selectedIncident = matching
                    onIncidentClick?.invoke(matching)
                }
                false
            }
        }
    }

    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView?.onStart()
                Lifecycle.Event.ON_RESUME -> mapView?.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView?.onPause()
                Lifecycle.Event.ON_STOP -> mapView?.onStop()
                Lifecycle.Event.ON_DESTROY -> mapView?.onDestroy()
                else -> {}
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            mapView?.onDestroy()
        }
    }

    val verifiedCount = remember(incidents) { incidents.count { it.status.equals("verified", ignoreCase = true) } }
    val reportedCount = remember(incidents) { incidents.count { !it.status.equals("verified", ignoreCase = true) } }

    Box(modifier = modifier) {
        AndroidView(
            factory = { ctx ->
                MapView(ctx).also { mv ->
                    mapView = mv
                    mv.onCreate(null)
                    mv.getMapAsync { map ->
                        mapboxMap = map
                        map.uiSettings.apply {
                            isZoomGesturesEnabled = true
                            isScrollGesturesEnabled = true
                            isTiltGesturesEnabled = true
                            isRotateGesturesEnabled = true
                            isCompassEnabled = false
                            isAttributionEnabled = false
                            isLogoEnabled = false
                        }
                        map.setStyle("https://tiles.openfreemap.org/styles/liberty") { _ ->
                            // Center camera on latest live incident if present, else user location, else default
                            val target = when {
                                incidents.isNotEmpty() -> LatLng(incidents.first().lat, incidents.first().lng)
                                location?.latitude != null && location.longitude != null -> LatLng(location.latitude, location.longitude)
                                else -> LatLng(19.076, 72.877) // Mumbai default
                            }
                            map.cameraPosition = CameraPosition.Builder()
                                .target(target)
                                .zoom(if (incidents.isNotEmpty()) 10.0 else if (location?.latitude != null) CAMERA_ZOOM_REGION else CAMERA_ZOOM_STATE)
                                .build()
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // Top Filter Bar
        Column(
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (isEmergencyMode) {
                ClaySurface(
                    color = EmergencyRed.copy(alpha = 0.96f),
                    shape = RoundedCornerShape(12.dp),
                    depth = 6.dp,
                    contentColor = CanvasLight
                ) {
                    Row(modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)) {
                        Icon(Icons.Filled.Warning, null, tint = CanvasLight, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text(T("map.evacMode"), style = MaterialTheme.typography.labelSmall, color = CanvasLight, fontWeight = FontWeight.Bold)
                    }
                }
            }

            // Category filter chips
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ClayChip(
                    label = "ALL (${incidents.size})",
                    color = if (activeFilter == "ALL") PrimaryGreen else CanvasLight,
                    modifier = Modifier.clickable {
                        activeFilter = "ALL"
                        if (incidents.isNotEmpty()) {
                            val avgLat = incidents.map { it.lat }.average()
                            val avgLng = incidents.map { it.lng }.average()
                            mapboxMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(avgLat, avgLng), 9.0))
                        }
                    }
                )

                if (verifiedCount > 0) {
                    ClayChip(
                        label = "VERIFIED ($verifiedCount)",
                        color = if (activeFilter == "VERIFIED") Color(0xFF10B981) else CanvasLight,
                        modifier = Modifier.clickable {
                            activeFilter = "VERIFIED"
                            val v = incidents.filter { it.status.equals("verified", ignoreCase = true) }
                            if (v.isNotEmpty()) {
                                mapboxMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(v.first().lat, v.first().lng), 11.0))
                            }
                        }
                    )
                }

                if (reportedCount > 0) {
                    ClayChip(
                        label = "REPORTED ($reportedCount)",
                        color = if (activeFilter == "REPORTED") WarningAmber else CanvasLight,
                        modifier = Modifier.clickable {
                            activeFilter = "REPORTED"
                            val r = incidents.filter { !it.status.equals("verified", ignoreCase = true) }
                            if (r.isNotEmpty()) {
                                mapboxMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(r.first().lat, r.first().lng), 11.0))
                            }
                        }
                    )
                }

                ClayChip(
                    label = "ZONES (${riskZones.size})",
                    color = if (activeFilter == "RISK") RiskModerate else CanvasLight,
                    modifier = Modifier.clickable {
                        activeFilter = "RISK"
                        if (riskZones.isNotEmpty()) {
                            mapboxMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(riskZones.first().lat, riskZones.first().lng), 11.0))
                        }
                    }
                )
            }
        }

        // Right side control buttons
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // My Location button
            ClaySurface(
                color = CanvasLight.copy(alpha = 0.96f),
                shape = RoundedCornerShape(12.dp),
                depth = 6.dp,
                onClick = onMyLocationClick
            ) {
                Row(modifier = Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.MyLocation, contentDescription = "My Location", tint = PrimaryGreen, modifier = Modifier.size(18.dp))
                }
            }

            // Center on Incidents button
            if (incidents.isNotEmpty()) {
                ClaySurface(
                    color = CanvasLight.copy(alpha = 0.96f),
                    shape = RoundedCornerShape(12.dp),
                    depth = 6.dp,
                    onClick = {
                        val firstInc = incidents.first()
                        mapboxMap?.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(firstInc.lat, firstInc.lng), 12.0))
                    }
                ) {
                    Row(modifier = Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.WarningAmber, contentDescription = "Center Incidents", tint = EmergencyRed, modifier = Modifier.size(18.dp))
                    }
                }
            }

            // Sync / Refresh incidents button
            if (onRefreshIncidents != null) {
                val infiniteTransition = rememberInfiniteTransition(label = "spin")
                val angle by infiniteTransition.animateFloat(
                    initialValue = 0f,
                    targetValue = 360f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(800, easing = LinearEasing),
                        repeatMode = RepeatMode.Restart
                    ),
                    label = "rot"
                )

                ClaySurface(
                    color = CanvasLight.copy(alpha = 0.96f),
                    shape = RoundedCornerShape(12.dp),
                    depth = 6.dp,
                    onClick = onRefreshIncidents
                ) {
                    Row(modifier = Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Outlined.Sync,
                            contentDescription = "Sync Swagger Incidents",
                            tint = PrimaryGreen,
                            modifier = Modifier
                                .size(18.dp)
                                .then(if (isRefreshing) Modifier.rotate(angle) else Modifier)
                        )
                    }
                }
            }
        }

        // Bottom Left Coordinates & Status
        ClaySurface(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(12.dp),
            shape = RoundedCornerShape(14.dp),
            color = CanvasLight.copy(alpha = 0.96f),
            depth = 6.dp
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.LocationOn, null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(6.dp))
                Column {
                    Text(
                        if (incidents.isNotEmpty()) "${incidents.size} Incidents on Map" else T("map.locating"),
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "Render Swagger Feed • Live Sync",
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                        color = PrimaryGreen
                    )
                }
                Spacer(Modifier.width(10.dp))
                DataSourceBadge(if (incidents.isNotEmpty()) "live" else "synthetic")
            }
        }

        // Floating Incident Detail Preview Card
        AnimatedVisibility(
            visible = selectedIncident != null,
            enter = fadeIn(tween(200)) + slideInVertically(tween(250)) { it / 2 },
            exit = fadeOut(tween(150)) + slideOutVertically(tween(200)) { it / 2 },
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            selectedIncident?.let { inc ->
                val isVerified = inc.status.equals("verified", ignoreCase = true)
                val statusColor = if (isVerified) Color(0xFF10B981) else WarningAmber

                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = CanvasLight,
                    shadowElevation = 10.dp,
                    border = androidx.compose.foundation.BorderStroke(1.5.dp, statusColor.copy(alpha = 0.5f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = statusColor.copy(alpha = 0.15f)
                                ) {
                                    Text(
                                        if (isVerified) "✓ VERIFIED INCIDENT" else "⚠ PENDING REVIEW",
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Black),
                                        color = statusColor
                                    )
                                }
                                Spacer(Modifier.width(8.dp))
                                Surface(
                                    shape = RoundedCornerShape(8.dp),
                                    color = EmergencyRed.copy(alpha = 0.12f)
                                ) {
                                    Text(
                                        "SEV ${inc.severity}/5",
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 4.dp),
                                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Bold),
                                        color = EmergencyRed
                                    )
                                }
                            }

                            IconButton(
                                onClick = { selectedIncident = null },
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(Icons.Outlined.Close, contentDescription = "Close", tint = TextSecondaryLight, modifier = Modifier.size(16.dp))
                            }
                        }

                        Spacer(Modifier.height(8.dp))

                        Text(
                            inc.type.replace('_', ' ').uppercase(),
                            style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Black),
                            color = TextPrimaryLight
                        )

                        if (!inc.description.isNullOrBlank()) {
                            Spacer(Modifier.height(4.dp))
                            Text(
                                inc.description,
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondaryLight,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis
                            )
                        }

                        Spacer(Modifier.height(8.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                String.format("%.4f, %.4f", inc.lat, inc.lng),
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                                color = TextSecondaryLight
                            )

                            Button(
                                onClick = {
                                    mapboxMap?.animateCamera(
                                        CameraUpdateFactory.newLatLngZoom(LatLng(inc.lat, inc.lng), 14.0)
                                    )
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = PrimaryGreen),
                                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier.height(28.dp)
                            ) {
                                Icon(Icons.Filled.ZoomIn, contentDescription = null, modifier = Modifier.size(14.dp), tint = CanvasLight)
                                Spacer(Modifier.width(4.dp))
                                Text("FOCUS", fontSize = 10.sp, fontWeight = FontWeight.Bold, color = CanvasLight)
                            }
                        }
                    }
                }
            }
        }
    }
}
