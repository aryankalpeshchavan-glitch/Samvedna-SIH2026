package com.crisiscore.app.ui.components

import android.graphics.Canvas
import android.graphics.Color as AColor
import android.graphics.Paint
import android.graphics.Bitmap
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
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
import org.maplibre.android.maps.Style

private const val CAMERA_ZOOM_REGION = 12.0
private const val CAMERA_ZOOM_STATE = 7.0

private fun buildRiskIcon(accent: Color): Bitmap {
    val size = 64
    val cx = size / 2f
    val cy = size / 2f
    val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
    val c = Canvas(bmp)
    val fill = Paint(Paint.ANTI_ALIAS_FLAG)
    fill.color = accent.toArgb()
    val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 3.6f
        color = AColor.WHITE
    }
    val shadow = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = AColor.argb(80, 20, 20, 16)
    }
    val gloss = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = AColor.argb(70, 255, 255, 255)
    }
    c.drawCircle(cx, cy, 18f, shadow)
    c.drawCircle(cx, cy, 16f, fill)
    c.drawCircle(cx, cy, 13.4f, ring)
    c.drawCircle(cx - 5f, cy - 5f, 5.5f, gloss)
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
    isEmergencyMode: Boolean,
    onMyLocationClick: () -> Unit,
    onEmergencyToggle: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var mapView by remember { mutableStateOf<MapView?>(null) }
    var mapboxMap by remember { mutableStateOf<MapLibreMap?>(null) }
    val iconCache = remember { mutableMapOf<String, org.maplibre.android.annotations.Icon>() }

    fun iconFor(level: String): org.maplibre.android.annotations.Icon {
        val key = level.uppercase()
        return iconCache.getOrPut(key) {
            val bmp = buildRiskIcon(riskLevelColor(key))
            IconFactory.getInstance(context).fromBitmap(bmp)
        }
    }

    LaunchedEffect(Unit) {
        try {
            org.maplibre.android.MapLibre.getInstance(context)
        } catch (_: Exception) { }
    }

    LaunchedEffect(location) {
        mapboxMap?.let { map ->
            if (location?.latitude != null && location.longitude != null) {
                val target = LatLng(location.latitude, location.longitude)
                map.animateCamera(CameraUpdateFactory.newLatLngZoom(target, CAMERA_ZOOM_REGION))
            }
        }
    }

    LaunchedEffect(location, riskZones, isEmergencyMode) {
        mapboxMap?.let { map ->
            map.clear()
            if (location?.latitude != null && location.longitude != null) {
                val latLng = LatLng(location.latitude, location.longitude)
                map.addMarker(
                    MarkerOptions()
                        .position(latLng)
                        .icon(iconFor("SAFE"))
                        .title(T.get("map.yourLocation"))
                        .snippet(T.get("map.gpsAccuracy").replace("{m}", "${location.accuracy?.toInt() ?: "?"}"))
                )
            }
            riskZones.forEach { zone ->
                val latLng = LatLng(zone.lat, zone.lng)
                val level = zone.risk_level.ifBlank { "LOW" }.uppercase()
                val title = zone.name ?: T.get("home.riskZone")
                map.addMarker(
                    MarkerOptions()
                        .position(latLng)
                        .icon(iconFor(level))
                        .title("$title \u2014 $level")
                        .snippet(T.get("map.riskScore").replace("{n}", "${zone.risk_score.toInt()}"))
                )
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

    val counts = remember(riskZones) {
        riskZones.groupingBy { it.risk_level.ifBlank { "LOW" }.uppercase() }.eachCount()
    }

    var selectedLevel by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(selectedLevel) {
        val level = selectedLevel ?: return@LaunchedEffect
        val matchingZones = riskZones.filter {
            it.risk_level.uppercase() == level ||
            (level == "MEDIUM" && it.risk_level.uppercase() == "WATCH")
        }
        if (matchingZones.isEmpty()) return@LaunchedEffect
        val map = mapboxMap ?: return@LaunchedEffect
        val avgLat = matchingZones.map { it.lat }.average()
        val avgLng = matchingZones.map { it.lng }.average()
        map.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(avgLat, avgLng), CAMERA_ZOOM_REGION))
    }

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
                            val target = if (location?.latitude != null && location.longitude != null) {
                                LatLng(location.latitude, location.longitude)
                            } else {
                                LatLng(26.14, 91.73)
                            }
                            map.cameraPosition = CameraPosition.Builder()
                                .target(target)
                                .zoom(if (location?.latitude != null) CAMERA_ZOOM_REGION else CAMERA_ZOOM_STATE)
                                .build()
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxSize()
        )

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

            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                listOf("CRITICAL" to RiskCritical, "HIGH" to RiskHigh, "MEDIUM" to RiskModerate, "LOW" to RiskLow)
                    .forEach { (level, color) ->
                        val count = (counts[level] ?: 0) + when (level) {
                            "MEDIUM" -> counts["WATCH"] ?: 0
                            else -> 0
                        }
                        val isSelected = selectedLevel == level
                        ClayChip(
                            label = if (count > 0) "$level $count" else level,
                            color = if (isSelected) CanvasLight else color,
                            modifier = Modifier
                                .graphicsLayer {
                                    alpha = if (count > 0) 1f else 0.55f
                                    scaleX = if (isSelected) 1.08f else 1f
                                    scaleY = if (isSelected) 1.08f else 1f
                                }
                                .then(
                                    if (count > 0) Modifier.clickable {
                                        selectedLevel = if (isSelected) null else level
                                    } else Modifier
                                )
                        )
                    }
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            ClaySurface(
                color = CanvasLight.copy(alpha = 0.96f),
                shape = RoundedCornerShape(12.dp),
                depth = 6.dp,
                onClick = onMyLocationClick
            ) {
                Row(modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.MyLocation, null, tint = PrimaryGreen, modifier = Modifier.size(18.dp))
                }
            }
        }

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
                        if (location?.latitude != null) {
                            String.format("%.4f\u00b0 N, %.4f\u00b0 E", location.latitude, location.longitude)
                        } else T("map.locating"),
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        when {
                            location?.accuracy != null -> "\u00b1${String.format("%.0f", location.accuracy)}m " + T("map.mAccuracy")
                            location?.isFallbackLocation == true -> T("map.gpsUnavailable")
                            else -> T("map.requestingGps")
                        },
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp),
                        color = TextSecondaryLight
                    )
                }
                Spacer(Modifier.width(10.dp))
                DataSourceBadge("synthetic")
            }
        }
    }
}

