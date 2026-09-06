package com.crisiscore.app.ui.screens.incident

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.IncidentCategory
import com.crisiscore.app.data.model.LocationData
import com.crisiscore.app.data.model.SeverityLevel
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import kotlinx.coroutines.launch

@Composable
fun IncidentScreen(
    repository: CrisisCoreRepository,
    onSubmit: (IncidentCategory, SeverityLevel, String) -> Unit
) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var selectedCategory by remember { mutableStateOf(IncidentCategory.LANDSLIDE) }
    var severity by remember { mutableStateOf(SeverityLevel.WATCH) }
    var note by remember { mutableStateOf("") }
    var photoUri by remember { mutableStateOf<Uri?>(null) }
    var submitted by remember { mutableStateOf(false) }
    var location by remember { mutableStateOf<LocationData?>(null) }

    val galleryLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        photoUri = uri
    }

    LaunchedEffect(Unit) {
        location = repository.getCurrentLocation()
    }

    val locationText = when {
        location?.latitude != null -> String.format("%.4f\u00b0 N, %.4f\u00b0 E", location!!.latitude, location!!.longitude)
        location?.isFallbackLocation == true -> "GPS unavailable \u2022 Enter manually"
        else -> "Detecting..."
    }

    if (submitted) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(72.dp)
                        .clip(RoundedCornerShape(36.dp))
                        .background(PrimaryGreen.copy(alpha = 0.1f))
                        .border(2.dp, PrimaryGreen, RoundedCornerShape(36.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Filled.CheckCircle, null, tint = PrimaryGreen, modifier = Modifier.size(40.dp))
                }
                Text(T.get("report.successTitle"), style = MaterialTheme.typography.headlineMedium)
                Text(
                    T.get("report.successMessage").replace("{category}", selectedCategory.name),
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondaryLight,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                    modifier = Modifier.padding(horizontal = 32.dp)
                )
                Spacer(Modifier.height(16.dp))
                CcButton(onClick = { submitted = false }, variant = CcButtonVariant.Secondary) {
                    Text(T.get("report.anotherButton"))
                }
            }
        }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        PageHeader(tag = T.get("report.subtitle"), title = T.get("report.title"))

        // 1. Category Grid
        Column {
            Text(T.get("report.step1"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight, modifier = Modifier.padding(bottom = 8.dp))
            val categories = listOf(
                IncidentCategory.LANDSLIDE to Icons.Filled.Terrain,
                IncidentCategory.SLOPE_CRACK to Icons.Filled.Warning,
                IncidentCategory.ROAD_BLOCKED to Icons.Filled.Block,
                IncidentCategory.FLOOD to Icons.Filled.WaterDrop,
                IncidentCategory.BUILDING_DAMAGE to Icons.Filled.Home,
                IncidentCategory.PERSON_TRAPPED to Icons.Filled.PersonOff,
                IncidentCategory.OTHER to Icons.Filled.MedicalServices
            )
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                categories.chunked(2).forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        row.forEach { (cat, icon) ->
                            val isSelected = selectedCategory == cat
                            Surface(
                                modifier = Modifier
                                    .weight(1f)
                                    .height(72.dp)
                                    .clip(RoundedCornerShape(14.dp))
                                    .clickable { selectedCategory = cat },
                                shape = RoundedCornerShape(14.dp),
                                color = if (isSelected) PrimaryGreen else SurfaceLight,
                                border = if (isSelected) null else ButtonDefaults.outlinedButtonBorder()
                            ) {
                                Column(
                                    modifier = Modifier.padding(10.dp),
                                    verticalArrangement = Arrangement.Center
                                ) {
                                    Icon(
                                        icon, null,
                                        tint = if (isSelected) CanvasLight else PrimaryGreen,
                                        modifier = Modifier.size(20.dp)
                                    )
                                    Spacer(Modifier.height(4.dp))
                                    Text(
                                        cat.name.replace("_", " "),
                                        style = MaterialTheme.typography.bodySmall.copy(
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 10.sp
                                        ),
                                        color = if (isSelected) CanvasLight else TextPrimaryLight
                                    )
                                }
                            }
                        }
                        if (row.size < 2) {
                            Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }

        // 2. Photo Upload
        Column {
            Text(T.get("report.step2"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight, modifier = Modifier.padding(bottom = 8.dp))
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(100.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .clickable { galleryLauncher.launch("image/*") },
                shape = RoundedCornerShape(14.dp),
                color = SurfaceLight,
                border = ButtonDefaults.outlinedButtonBorder()
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    if (photoUri != null) {
                        Icon(Icons.Filled.CheckCircle, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                        Spacer(Modifier.height(4.dp))
                        Text(T.get("report.photoAttached"), style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = PrimaryGreen)
                    } else {
                        Icon(Icons.Filled.CameraAlt, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                        Spacer(Modifier.height(4.dp))
                        Text(T.get("report.uploadPhoto"), style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
                        Text(T.get("report.uploadLimit"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
                    }
                }
            }
        }

        // 3. Location
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            borderColor = if (location?.latitude != null) PrimaryGreen else WarningAmber.copy(alpha = 0.5f)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.LocationOn, null, tint = PrimaryGreen, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("${T.get("report.gpsLabel")} ${T.get("report.gpsAuto")}", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
                    if (location?.accuracy != null) {
                        Text("Accuracy: \u00b1${String.format("%.0f", location!!.accuracy)}m", style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
                    } else if (location?.isFallbackLocation == true) {
                        Text("Manual location entry recommended", style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = WarningAmber)
                    }
                }
                Text(locationText, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), fontWeight = FontWeight.Bold, color = PrimaryGreen)
            }
        }

        // 4. Severity
        Column {
            Text(T.get("report.step4"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight, modifier = Modifier.padding(bottom = 8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(SeverityLevel.LOW, SeverityLevel.WATCH, SeverityLevel.CRITICAL).forEach { lvl ->
                    val isSelected = severity == lvl
                    val bgColor = when (lvl) {
                        SeverityLevel.CRITICAL -> EmergencyRed
                        SeverityLevel.WATCH -> WarningAmber
                        else -> PrimaryGreen
                    }
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clip(RoundedCornerShape(12.dp))
                            .clickable { severity = lvl },
                        shape = RoundedCornerShape(12.dp),
                        color = if (isSelected) bgColor else SurfaceLight,
                        border = if (isSelected) null else ButtonDefaults.outlinedButtonBorder()
                    ) {
                        Text(
                            lvl.name,
                            modifier = Modifier.padding(vertical = 12.dp),
                            style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                            color = if (isSelected) CanvasLight else TextPrimaryLight,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center
                        )
                    }
                }
            }
        }

        // 5. Notes
        Column {
            Text(T.get("report.step5"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight, modifier = Modifier.padding(bottom = 8.dp))
            OutlinedTextField(
                value = note,
                onValueChange = { note = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Describe what you see...", style = MaterialTheme.typography.bodySmall) },
                minLines = 3,
                shape = RoundedCornerShape(12.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    unfocusedBorderColor = BorderLight,
                    focusedBorderColor = PrimaryGreen,
                    unfocusedContainerColor = SurfaceLight,
                    focusedContainerColor = SurfaceLight
                )
            )
        }

        // Submit
        CcButton(
            onClick = { onSubmit(selectedCategory, severity, note) },
            variant = CcButtonVariant.Secondary,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Filled.Send, null, modifier = Modifier.size(16.dp))
            Spacer(Modifier.width(8.dp))
            Text(T.get("report.submitButton"))
        }

        Spacer(Modifier.height(80.dp))
    }
}
