package com.crisiscore.app.ui.components

import android.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
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
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.Style

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

    LaunchedEffect(Unit) {
        try {
            MapLibre.getInstance(context)
        } catch (_: Exception) { }
    }

    LaunchedEffect(location) {
        mapboxMap?.let { map ->
            if (location?.latitude != null && location.longitude != null) {
                val target = LatLng(location.latitude, location.longitude)
                map.animateCamera(CameraUpdateFactory.newLatLngZoom(target, 12.0))
            }
        }
    }

    LaunchedEffect(location, isEmergencyMode) {
        mapboxMap?.let { map ->
            map.clear()
            if (location?.latitude != null && location.longitude != null) {
                val latLng = LatLng(location.latitude, location.longitude)
                map.addMarker(
                    org.maplibre.android.annotations.MarkerOptions()
                        .position(latLng)
                        .title("Your Location")
                )
            }
            riskZones.forEach { zone ->
                val latLng = LatLng(zone.lat, zone.lng)
                val title = when {
                    zone.risk_level.contains("CRITICAL", true) -> "CRITICAL Risk Zone"
                    zone.risk_level.contains("HIGH", true) -> "High Risk Zone"
                    zone.risk_level.contains("MEDIUM", true) || zone.risk_level.contains("WATCH", true) -> "Moderate Risk Zone"
                    else -> "Low Risk Zone"
                }
                map.addMarker(
                    org.maplibre.android.annotations.MarkerOptions()
                        .position(latLng)
                        .title(title)
                        .snippet("Risk Score: ${zone.risk_score}")
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
                        map.setStyle(Style.getPredefinedStyle("Streets")) { _ ->
                            if (location?.latitude != null && location.longitude != null) {
                                map.cameraPosition = CameraPosition.Builder()
                                    .target(LatLng(location.latitude, location.longitude))
                                    .zoom(12.0)
                                    .build()
                            } else {
                                map.cameraPosition = CameraPosition.Builder()
                                    .target(LatLng(26.14, 91.73))
                                    .zoom(7.0)
                                    .build()
                            }
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
            Surface(
                shape = RoundedCornerShape(10.dp),
                color = CanvasLight.copy(alpha = 0.92f),
                shadowElevation = 2.dp
            ) {
                Row(modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)) {
                    Icon(Icons.Outlined.Language, null, tint = PrimaryGreen, modifier = Modifier.size(16.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("NORTH EASTERN REGION", style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)
                }
            }
            if (isEmergencyMode) {
                Surface(
                    shape = RoundedCornerShape(10.dp),
                    color = EmergencyRed.copy(alpha = 0.92f),
                    shadowElevation = 2.dp
                ) {
                    Row(modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp)) {
                        Icon(Icons.Filled.Warning, null, tint = CanvasLight, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("EVACUATION MODE", style = MaterialTheme.typography.labelSmall, color = CanvasLight, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            MapFloatingButton(Icons.Outlined.MyLocation, "My Location") { onMyLocationClick() }
            MapFloatingButton(Icons.Filled.Layers, "Layers") { }
            MapFloatingButton(
                if (isEmergencyMode) Icons.Filled.Warning else Icons.Outlined.Warning,
                if (isEmergencyMode) "Exit" else "Emergency"
            ) { onEmergencyToggle() }
        }

        Surface(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(12.dp),
            shape = RoundedCornerShape(12.dp),
            color = CanvasLight.copy(alpha = 0.92f),
            shadowElevation = 3.dp
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
                        } else "Locating...",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        when {
                            location?.accuracy != null -> "\u00b1${String.format("%.0f", location.accuracy)}m accuracy"
                            location?.isFallbackLocation == true -> "GPS unavailable"
                            else -> "Requesting GPS..."
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

@Composable
private fun MapFloatingButton(
    icon: ImageVector,
    contentDescription: String,
    onClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(10.dp),
        color = CanvasLight.copy(alpha = 0.92f),
        shadowElevation = 3.dp,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(icon, contentDescription, tint = PrimaryGreen, modifier = Modifier.size(18.dp))
            Spacer(Modifier.height(2.dp))
            Text(contentDescription, style = MaterialTheme.typography.labelSmall.copy(fontSize = 7.sp), color = TextPrimaryLight)
        }
    }
}
