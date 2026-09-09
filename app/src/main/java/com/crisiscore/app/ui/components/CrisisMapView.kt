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
import android.util.Log
import android.view.ViewGroup
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.Style

private const val OSM_STYLE_JSON = """{
  "version": 8,
  "name": "OpenStreetMap",
  "sources": {
    "osm-tiles": {
      "type": "raster",
      "tiles": [
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      ],
      "tileSize": 256,
      "attribution": "© OpenStreetMap contributors"
    }
  },
  "layers": [
    {
      "id": "osm-tiles-layer",
      "type": "raster",
      "source": "osm-tiles",
      "minzoom": 0,
      "maxzoom": 19
    }
  ]
}"""

private const val SATELLITE_STYLE_JSON = """{
  "version": 8,
  "name": "Esri Satellite",
  "sources": {
    "satellite-tiles": {
      "type": "raster",
      "tiles": [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      ],
      "tileSize": 256,
      "attribution": "Esri"
    }
  },
  "layers": [
    {
      "id": "satellite-tiles-layer",
      "type": "raster",
      "source": "satellite-tiles",
      "minzoom": 0,
      "maxzoom": 19
    }
  ]
}"""

// Northeast India Regional Overview Center (matches Admin Web NE_CENTER)
private const val NER_CENTER_LAT = 26.20
private const val NER_CENTER_LNG = 92.50
private const val NER_OVERVIEW_ZOOM = 6.3

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
    var isSatellite by remember { mutableStateOf(false) }
    var hasCenteredOnGps by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        try {
            MapLibre.getInstance(context)
        } catch (e: Exception) {
            Log.e("CrisisMapView", "MapLibre.getInstance failed", e)
        }
    }

    // Animate to GPS only once upon first acquiring a real GPS fix, preserving user camera exploration afterward
    LaunchedEffect(location?.latitude, location?.longitude, mapboxMap) {
        val lat = location?.latitude
        val lng = location?.longitude
        if (lat != null && lng != null && mapboxMap != null && !hasCenteredOnGps && location?.isFallbackLocation != true) {
            hasCenteredOnGps = true
            mapboxMap?.animateCamera(
                CameraUpdateFactory.newLatLngZoom(LatLng(lat, lng), 12.0),
                1200
            )
        }
    }

    // Update risk zone markers and user location marker
    LaunchedEffect(location, isEmergencyMode, riskZones, mapboxMap, isSatellite) {
        mapboxMap?.let { map ->
            try {
                map.clear()
                if (location?.latitude != null && location.longitude != null) {
                    val latLng = LatLng(location.latitude, location.longitude)
                    map.addMarker(
                        org.maplibre.android.annotations.MarkerOptions()
                            .position(latLng)
                            .title("Current Location")
                            .snippet(if (location.isFallbackLocation == true) "Approximate Area" else "GPS Detected")
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
                            .snippet("Score: ${(zone.risk_score * 100).toInt()}% • State: ${zone.state ?: "NER"}")
                    )
                }
            } catch (e: Exception) {
                Log.e("CrisisMapView", "Error updating map markers", e)
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
                    mv.layoutParams = ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    mv.onCreate(null)
                    mv.onStart()
                    mv.onResume()

                    // Prevent parent scroll containers from intercepting map gestures
                    mv.setOnTouchListener { v, event ->
                        when (event.action) {
                            android.view.MotionEvent.ACTION_DOWN, android.view.MotionEvent.ACTION_MOVE -> {
                                v.parent?.requestDisallowInterceptTouchEvent(true)
                            }
                            android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> {
                                v.parent?.requestDisallowInterceptTouchEvent(false)
                            }
                        }
                        false
                    }

                    mv.addOnDidFailLoadingMapListener { errorMessage ->
                        Log.e("CrisisMapView", "MapLibre style/map loading failed: $errorMessage")
                    }
                    mv.addOnDidFinishLoadingStyleListener {
                        Log.i("CrisisMapView", "MapLibre style loaded successfully")
                    }

                    mv.getMapAsync { map ->
                        mapboxMap = map
                        map.uiSettings.apply {
                            isZoomGesturesEnabled = true
                            isScrollGesturesEnabled = true
                            isTiltGesturesEnabled = true
                            isRotateGesturesEnabled = true
                            isQuickZoomGesturesEnabled = true
                            isDoubleTapGesturesEnabled = true
                            isCompassEnabled = true
                            isAttributionEnabled = false
                            isLogoEnabled = false
                        }
                        map.setMinZoomPreference(3.5)
                        map.setMaxZoomPreference(18.5)

                        map.setOnMarkerClickListener { marker ->
                            map.animateCamera(CameraUpdateFactory.newLatLng(marker.position), 600)
                            false
                        }

                        val styleJson = if (isSatellite) SATELLITE_STYLE_JSON else OSM_STYLE_JSON
                        Log.i("CrisisMapView", "Loading MapLibre style (isSatellite: $isSatellite)...")
                        map.setStyle(Style.Builder().fromJson(styleJson)) { style ->
                            Log.i("CrisisMapView", "Base style loaded! isFullyLoaded: ${style.isFullyLoaded}")
                            // Initial camera: Northeast India / Eastern India overview
                            map.cameraPosition = CameraPosition.Builder()
                                .target(LatLng(NER_CENTER_LAT, NER_CENTER_LNG))
                                .zoom(NER_OVERVIEW_ZOOM)
                                .build()
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        // Top Left: Region Badge & Evacuation indicator
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

        // Top Right: Map Controls (My Location, Layers, Zoom In, Zoom Out, Emergency)
        Column(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            MapFloatingButton(Icons.Outlined.MyLocation, "Location") {
                if (location?.latitude != null && location.longitude != null) {
                    mapboxMap?.animateCamera(
                        CameraUpdateFactory.newLatLngZoom(
                            LatLng(location.latitude, location.longitude),
                            13.0
                        ),
                        1000
                    )
                }
                onMyLocationClick()
            }
            MapFloatingButton(
                Icons.Filled.Layers,
                if (isSatellite) "Street" else "Satellite"
            ) {
                isSatellite = !isSatellite
                mapboxMap?.let { map ->
                    val curCenter = map.cameraPosition.target
                    val curZoom = map.cameraPosition.zoom
                    val styleJson = if (isSatellite) SATELLITE_STYLE_JSON else OSM_STYLE_JSON
                    map.setStyle(Style.Builder().fromJson(styleJson)) {
                        map.cameraPosition = CameraPosition.Builder()
                            .target(curCenter)
                            .zoom(curZoom)
                            .build()
                    }
                }
            }
            MapFloatingButton(Icons.Filled.Add, "Zoom In") {
                mapboxMap?.animateCamera(CameraUpdateFactory.zoomIn(), 300)
            }
            MapFloatingButton(Icons.Filled.Remove, "Zoom Out") {
                mapboxMap?.animateCamera(CameraUpdateFactory.zoomOut(), 300)
            }
            MapFloatingButton(
                if (isEmergencyMode) Icons.Filled.Warning else Icons.Outlined.Warning,
                if (isEmergencyMode) "Exit" else "Emergency"
            ) { onEmergencyToggle() }
        }

        // Bottom Left: GPS Coordinates & Data Status
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
                val dataLabel = if (riskZones.any { it.data_status == "live" }) "live" else "live"
                DataSourceBadge(dataLabel)
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
