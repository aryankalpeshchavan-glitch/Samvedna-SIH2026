package com.crisiscore.app.ui.screens.incident

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.vector.ImageVector
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
        location?.isFallbackLocation == true -> T("report.gpsManual")
        else -> T("report.gpsAcquiring")
    }

    if (submitted) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            ClaySurface(
                color = CanvasLight,
                modifier = Modifier.padding(24.dp),
                shape = ClayShapes.cardLarge,
                depth = 12.dp
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Box(
                        modifier = Modifier
                            .size(80.dp)
                            .clip(RoundedCornerShape(40.dp))
                            .background(PrimaryGreen.copy(alpha = 0.1f))
                            .border(2.dp, PrimaryGreen, RoundedCornerShape(40.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Filled.CheckCircle, null, tint = PrimaryGreen, modifier = Modifier.size(44.dp))
                    }
                    Text(T("report.successTitle"), style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Black)
                    Text(
                        T("report.successMessage").replace("{category}", selectedCategory.name.replace("_", " ")),
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondaryLight,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 16.dp)
                    )
                    Spacer(Modifier.height(8.dp))
                    CcButton(onClick = { submitted = false }, variant = CcButtonVariant.Secondary) {
                        Text(T("report.anotherButton"))
                    }
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
        PageHeader(tag = T("report.subtitle"), title = T("report.title"))

        // Step indicator
        StepIndicator(currentStep = 1, totalSteps = 4)

        // 1. Category Selection
        ReportSection(
            title = T("report.step1"),
            subtitle = T("report.step1Sub"),
            icon = Icons.Filled.Category
        ) {
            val categories = listOf(
                IncidentCategory.LANDSLIDE to Icons.Filled.Terrain,
                IncidentCategory.SLOPE_CRACK to Icons.Filled.Warning,
                IncidentCategory.ROAD_BLOCKED to Icons.Filled.Block,
                IncidentCategory.FLOOD to Icons.Filled.WaterDrop,
                IncidentCategory.BUILDING_DAMAGE to Icons.Filled.Home,
                IncidentCategory.PERSON_TRAPPED to Icons.Filled.PersonOff,
                IncidentCategory.OTHER to Icons.Filled.MedicalServices
            )
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                categories.chunked(2).forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        row.forEach { (cat, icon) ->
                            val isSelected = selectedCategory == cat
                            CategoryTile(
                                category = cat,
                                icon = icon,
                                isSelected = isSelected,
                                modifier = Modifier.weight(1f),
                                onClick = { selectedCategory = cat }
                            )
                        }
                        if (row.size < 2) {
                            Spacer(Modifier.weight(1f))
                        }
                    }
                }
            }
        }

        // 2. Photo Upload
        ReportSection(
            title = T("report.step2"),
            subtitle = T("report.step2Sub"),
            icon = Icons.Filled.CameraAlt
        ) {
            PhotoUploadTile(
                photoUri = photoUri,
                onClick = { galleryLauncher.launch("image/*") }
            )
        }

        // 3. Location
        ReportSection(
            title = T("report.step3"),
            subtitle = T("report.step3Sub"),
            icon = Icons.Filled.LocationOn
        ) {
            LocationTile(location = location, locationText = locationText)
        }

        // 4. Severity
        ReportSection(
            title = T("report.step4"),
            subtitle = T("report.step4Sub"),
            icon = Icons.Filled.PriorityHigh
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                listOf(SeverityLevel.LOW, SeverityLevel.WATCH, SeverityLevel.CRITICAL).forEach { lvl ->
                    val isSelected = severity == lvl
                    val bgColor = when (lvl) {
                        SeverityLevel.CRITICAL -> EmergencyRed
                        SeverityLevel.WATCH -> WarningAmber
                        else -> PrimaryGreen
                    }
                    ClaySurface(
                        color = if (isSelected) bgColor else SurfaceLight,
                        modifier = Modifier.weight(1f).height(56.dp),
                        shape = ClayShapes.button,
                        depth = if (isSelected) 5.dp else 2.dp,
                        tint = if (isSelected) null else BorderLight,
                        contentColor = if (isSelected) CanvasLight else TextPrimaryLight,
                        onClick = { severity = lvl }
                    ) {
                        Row(
                            modifier = Modifier.fillMaxSize(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                when (lvl) {
                                    SeverityLevel.CRITICAL -> Icons.Filled.Error
                                    SeverityLevel.WATCH -> Icons.Filled.WarningAmber
                                    else -> Icons.Filled.CheckCircle
                                },
                                contentDescription = null,
                                tint = if (isSelected) CanvasLight else bgColor,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(Modifier.width(6.dp))
                            Text(
                                lvl.name,
                                style = MaterialTheme.typography.labelMedium.copy(fontWeight = FontWeight.Bold),
                                color = if (isSelected) CanvasLight else TextPrimaryLight
                            )
                        }
                    }
                }
            }
        }

        // 5. Notes
        ReportSection(
            title = T("report.step5"),
            subtitle = T("report.step5Sub"),
            icon = Icons.Filled.Notes
        ) {
            OutlinedTextField(
                value = note,
                onValueChange = { note = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text(T("report.notesPlaceholder"), style = MaterialTheme.typography.bodySmall) },
                minLines = 3,
                shape = ClayShapes.control,
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
            onClick = { onSubmit(selectedCategory, severity, note); submitted = true },
            variant = CcButtonVariant.Emergency,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Filled.Send, null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text(T("report.submitButton"), fontWeight = FontWeight.Black)
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun StepIndicator(currentStep: Int, totalSteps: Int) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        (1..totalSteps).forEach { step ->
            val isActive = step <= currentStep
            val isCurrent = step == currentStep
            Column(
                modifier = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(if (isCurrent) 28.dp else 20.dp)
                        .graphicsLayer { scaleX = if (isCurrent) 1.2f else 1f; scaleY = if (isCurrent) 1.2f else 1f }
                        .clip(CircleShape)
                        .background(if (isActive) PrimaryGreen else BorderLight),
                    contentAlignment = Alignment.Center
                ) {
                    if (isActive) {
                        Icon(Icons.Filled.Check, null, tint = CanvasLight, modifier = Modifier.size(12.dp))
                    }
                }
                if (step < totalSteps) {
                    Box(
                        modifier = Modifier
                            .width(16.dp)
                            .height(2.dp)
                            .background(if (step < currentStep) PrimaryGreen else BorderLight)
                    )
                }
            }
        }
    }
}

@Composable
private fun ReportSection(
    title: String,
    subtitle: String,
    icon: ImageVector,
    content: @Composable () -> Unit
) {
    ClaySurface(
        color = ClayCreamTint,
        modifier = Modifier.fillMaxWidth(),
        shape = ClayShapes.card,
        depth = 6.dp,
        tint = BorderLight.copy(alpha = 0.3f)
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(icon, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(title, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Black, color = TextPrimaryLight)
                    Text(subtitle, style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp), color = TextSecondaryLight)
                }
            }
            content()
        }
    }
}

@Composable
private fun CategoryTile(
    category: IncidentCategory,
    icon: ImageVector,
    isSelected: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    ClaySurface(
        color = if (isSelected) PrimaryGreen else SurfaceLight,
        modifier = modifier
            .height(80.dp)
            .fillMaxWidth(),
        shape = ClayShapes.control,
        depth = if (isSelected) 6.dp else 2.dp,
        tint = if (isSelected) null else BorderLight,
        contentColor = if (isSelected) CanvasLight else TextPrimaryLight,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(12.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                icon, null,
                tint = if (isSelected) CanvasLight else PrimaryGreen,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.height(6.dp))
            Text(
                T("cat.${category.name}"),
                style = MaterialTheme.typography.bodySmall.copy(
                    fontWeight = FontWeight.Bold,
                    fontSize = 10.sp
                ),
                color = if (isSelected) CanvasLight else TextPrimaryLight,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                maxLines = 2
            )
        }
    }
}

@Composable
private fun PhotoUploadTile(
    photoUri: Uri?,
    onClick: () -> Unit
) {
    ClaySurface(
        color = SurfaceLight,
        modifier = Modifier.fillMaxWidth().height(110.dp),
        shape = ClayShapes.control,
        depth = 2.dp,
        tint = BorderLight,
        contentColor = PrimaryGreen,
        onClick = onClick
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            if (photoUri != null) {
                Row(horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.CheckCircle, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(8.dp))
                    Text(T("report.photoAttached"), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold, color = PrimaryGreen)
                }
                Text(T("report.tapToChange"), style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight)
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Filled.CameraAlt, null, tint = PrimaryGreen, modifier = Modifier.size(32.dp))
                    Spacer(Modifier.height(8.dp))
                    Text(T("report.uploadPhoto"), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold, color = PrimaryGreen)
                    Text(T("report.uploadLimit"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
                }
            }
        }
    }
}

@Composable
private fun LocationTile(
    location: LocationData?,
    locationText: String
) {
    val hasFix = location?.latitude != null
    ClaySurface(
        color = if (hasFix) ClayGreenTint.copy(alpha = 0.15f) else ClayAmberTint.copy(alpha = 0.15f),
        modifier = Modifier.fillMaxWidth(),
        shape = ClayShapes.control,
        depth = 2.dp,
        tint = if (hasFix) PrimaryGreen else WarningAmber,
        contentColor = if (hasFix) PrimaryGreen else WarningAmber
    ) {
        Row(
            modifier = Modifier.padding(14.dp).fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Filled.LocationOn, null, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    "${T("report.gpsLabel")} ${T("report.gpsAuto")}",
                    style = MaterialTheme.typography.bodySmall,
                    fontWeight = FontWeight.Bold,
                    color = if (hasFix) PrimaryGreen else WarningAmber
                )
                if (location?.accuracy != null) {
                    Text(T("report.gpsAccuracy").replace("{m}", String.format("%.0f", location!!.accuracy)), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
                } else if (location?.isFallbackLocation == true) {
                    Text(T("report.gpsManual"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = WarningAmber)
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(locationText, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), fontWeight = FontWeight.Bold, color = if (hasFix) PrimaryGreen else WarningAmber)
                Text(if (hasFix) T("report.gpsFixAcquired") else T("report.gpsAcquiring"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)
            }
        }
    }
}