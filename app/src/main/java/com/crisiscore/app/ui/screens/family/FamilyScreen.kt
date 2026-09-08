package com.crisiscore.app.ui.screens.family

import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.crisiscore.app.data.model.FamilyMember
import com.crisiscore.app.data.model.FamilyMemberStatus
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T

@Composable
fun FamilyScreen(
    viewModel: com.crisiscore.app.ui.viewmodel.FamilyViewModel = androidx.lifecycle.viewmodel.compose.viewModel()
) {
    val familyList by viewModel.familyList.collectAsState()
    var showAddMember by remember { mutableStateOf(false) }
    var showCheckInOthers by remember { mutableStateOf(false) }
    var showReportSomeone by remember { mutableStateOf(false) }
    var toastMessage by remember { mutableStateOf<String?>(null) }

    val checkedInCount = familyList.count { it.status == FamilyMemberStatus.CHECKED_IN }
    val percentAccounted = if (familyList.isNotEmpty()) (checkedInCount * 100 / familyList.size) else 0

    if (toastMessage != null) {
        LaunchedEffect(toastMessage) {
            kotlinx.coroutines.delay(2500)
            toastMessage = null
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 14.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T("family.communityMesh"), title = T("family.title"))

        if (familyList.isEmpty()) {
            EmptyFamilyState(onAddMember = { showAddMember = true })
        } else {
            FamilySummaryCard(familyList, checkedInCount, percentAccounted) {
                viewModel.markSelfSafe()
                toastMessage = T.get("family.youMarkedSafe")
            }

            ActionButtons(
                onCheckInOthers = { showCheckInOthers = true }
            )

            FamilyMemberHeader(familyList.size) { showAddMember = true }

            familyList.forEach { member ->
                FamilyMemberCard(member) {
                    toastMessage = T.get("family.smsCheckInSent").replace("{name}", member.name)
                }
            }

            CommunitySection(onReportSomeone = { showReportSomeone = true })
        }

        Spacer(Modifier.height(80.dp))
    }

    if (toastMessage != null) {
        Surface(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = 16.dp),
            shape = RoundedCornerShape(16.dp),
            color = PrimaryGreen,
            shadowElevation = 8.dp
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.CheckCircle, null, tint = CanvasLight, modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(8.dp))
                Text(toastMessage ?: "", color = CanvasLight, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
            }
        }
    }

    if (showAddMember) {
        AddMemberDialog(
            onDismiss = { showAddMember = false },
            onAdd = { name, rel ->
                viewModel.addMember(name, rel)
                toastMessage = T.get("family.addedToFamily").replace("{name}", name)
                showAddMember = false
            }
        )
    }

    if (showCheckInOthers) {
        CheckInOthersDialog(
            familyList = familyList.filter { !it.isSelf },
            onDismiss = { showCheckInOthers = false },
            onConfirm = { selectedIds ->
                viewModel.checkInMembers(selectedIds)
                toastMessage = T.get("family.checkedInCount").replace("{count}", selectedIds.size.toString())
                showCheckInOthers = false
            }
        )
    }

    if (showReportSomeone) {
        ReportSomeoneDialog(
            onDismiss = { showReportSomeone = false },
            onConfirm = { name ->
                toastMessage = T.get("family.reportSubmitted").replace("{name}", name.ifEmpty { "person" })
                showReportSomeone = false
            }
        )
    }
}
}

@Composable
private fun EmptyFamilyState(onAddMember: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 32.dp, horizontal = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Box(
            modifier = Modifier
                .size(80.dp)
                .clip(RoundedCornerShape(24.dp))
                .background(PrimaryGreen.copy(alpha = 0.08f)),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                Icons.Filled.People,
                null,
                tint = PrimaryGreen.copy(alpha = 0.4f),
                modifier = Modifier.size(40.dp)
            )
        }
        Spacer(Modifier.height(20.dp))
        Text(
            T("family.title"),
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Black,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(8.dp))
        Text(
            T("family.addMemberLabel"),
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondaryLight,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(24.dp))
        CcButton(onClick = onAddMember) {
            Icon(Icons.Filled.PersonAdd, null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text(T("family.addMemberLabel"), fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun FamilySummaryCard(
    familyList: List<FamilyMember>,
    checkedInCount: Int,
    percentAccounted: Int,
    onMarkSafe: () -> Unit
) {
    CcCard(modifier = Modifier.fillMaxWidth(), borderColor = PrimaryGreen.copy(alpha = 0.3f)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(PrimaryGreen.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.People, null, tint = PrimaryGreen, modifier = Modifier.size(22.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(T("family.statusSummary"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)
                Text(
                    T("family.summary")
                        .replace("{count}", checkedInCount.toString())
                        .replace("{total}", familyList.size.toString()),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Black
                )
            }
            Surface(
                shape = RoundedCornerShape(10.dp),
                color = PrimaryGreen.copy(alpha = 0.1f)
            ) {
                Text(
                    T("family.percentSafe").replace("{percent}", percentAccounted.toString()),
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
                    style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                    color = PrimaryGreen
                )
            }
        }
        Spacer(Modifier.height(12.dp))
        LinearProgressIndicator(
            progress = { percentAccounted / 100f },
            modifier = Modifier
                .fillMaxWidth()
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp)),
            color = PrimaryGreen,
            trackColor = BorderLight,
        )
    }
}

@Composable
private fun ActionButtons(onCheckInOthers: () -> Unit) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Surface(
            modifier = Modifier
                .weight(1f)
                .clip(RoundedCornerShape(14.dp))
                .background(PrimaryGreen),
            shape = RoundedCornerShape(14.dp),
            onClick = onCheckInOthers
        ) {
            Row(
                modifier = Modifier.padding(vertical = 14.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.CheckCircle, null, tint = CanvasLight, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text(T("family.imSafe"), color = CanvasLight, fontWeight = FontWeight.Black, fontSize = 13.sp)
            }
        }
        Surface(
            modifier = Modifier
                .weight(1f)
                .clip(RoundedCornerShape(14.dp)),
            shape = RoundedCornerShape(14.dp),
            color = CanvasLight,
            onClick = onCheckInOthers,
            border = ButtonDefaults.outlinedButtonBorder()
        ) {
            Row(
                modifier = Modifier.padding(vertical = 14.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(Icons.Filled.PersonAdd, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text(T("family.checkInOthersBtn"), color = PrimaryGreen, fontWeight = FontWeight.Bold, fontSize = 11.sp)
            }
        }
    }
}

@Composable
private fun FamilyMemberHeader(count: Int, onAddMember: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            T("family.membersCount").replace("{count}", count.toString()),
            style = MaterialTheme.typography.labelSmall,
            color = TextSecondaryLight
        )
        TextButton(onClick = onAddMember) {
            Icon(Icons.Filled.PersonAdd, null, modifier = Modifier.size(14.dp))
            Spacer(Modifier.width(4.dp))
            Text(
                T("family.addMemberLabel"),
                style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                color = PrimaryGreen
            )
        }
    }
}

@Composable
private fun FamilyMemberCard(member: FamilyMember, onRequestCheckIn: () -> Unit) {
    val isChecked = member.status == FamilyMemberStatus.CHECKED_IN
    val color = when {
        isChecked -> PrimaryGreen
        member.status == FamilyMemberStatus.NEEDS_CHECKIN -> WarningAmber
        else -> EmergencyRed
    }

    CcCard(
        modifier = Modifier
            .fillMaxWidth()
            .animateContentSize(spring(stiffness = Spring.StiffnessMediumLow))
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(color.copy(alpha = 0.1f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    when {
                        member.isSelf -> Icons.Filled.Shield
                        member.relationship in listOf("Son", "Daughter") -> Icons.Filled.Favorite
                        else -> Icons.Filled.Person
                    },
                    null, tint = color, modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(member.name, style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                    Spacer(Modifier.width(6.dp))
                    Surface(shape = RoundedCornerShape(6.dp), color = TextSecondaryLight.copy(alpha = 0.1f)) {
                        Text(
                            member.relationship,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                            color = TextSecondaryLight
                        )
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 3.dp)) {
                    Box(modifier = Modifier.size(6.dp).clip(RoundedCornerShape(3.dp)).background(color))
                    Spacer(Modifier.width(6.dp))
                    Text(
                        when {
                            isChecked -> "${member.checkedInBy ?: T("family.checkedIn")} \u2022 ${member.checkedInAt ?: "Just now"}"
                            member.status == FamilyMemberStatus.NEEDS_CHECKIN -> T("family.notCheckedIn")
                            else -> T("family.needsCheckIn")
                        },
                        style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp),
                        color = color,
                        fontWeight = FontWeight.Bold
                    )
                }
                if (member.location != null) {
                    Text(
                        member.location,
                        style = MaterialTheme.typography.bodySmall.copy(fontSize = 10.sp),
                        color = TextSecondaryLight,
                        modifier = Modifier.padding(top = 2.dp)
                    )
                }
            }
            if (!isChecked) {
                Surface(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .border(1.dp, PrimaryGreen.copy(alpha = 0.3f), RoundedCornerShape(8.dp)),
                    shape = RoundedCornerShape(8.dp),
                    color = CanvasLight,
                    onClick = onRequestCheckIn
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Filled.Phone, null, tint = PrimaryGreen, modifier = Modifier.size(12.dp))
                        Spacer(Modifier.width(4.dp))
                        Text(
                            T("family.checkIn"),
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                            color = PrimaryGreen,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun CommunitySection(onReportSomeone: () -> Unit) {
    Spacer(Modifier.height(12.dp))
    HorizontalDivider(color = BorderLight, thickness = 2.dp)
    Spacer(Modifier.height(8.dp))

    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Filled.Favorite, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp))
        Spacer(Modifier.width(8.dp))
        Text(T("family.helpSomeoneElse"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen)
    }

    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp)),
        shape = RoundedCornerShape(14.dp),
        color = SurfaceLight,
        onClick = onReportSomeone
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Filled.FavoriteBorder, null, tint = PrimaryGreen, modifier = Modifier.size(22.dp))
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(T("family.reportSomeoneSafe"), style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                Text(T("family.reportDescription"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
            }
        }
    }
}

@Composable
private fun AddMemberDialog(onDismiss: () -> Unit, onAdd: (String, String) -> Unit) {
    var name by remember { mutableStateOf("") }
    var relationship by remember { mutableStateOf("Relative") }
    val relationships = listOf(
        T("family.spouse"), T("family.son"), T("family.daughter"), T("family.father"),
        T("family.mother"), T("family.grandparent"), T("family.relative")
    )

    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = RoundedCornerShape(24.dp), color = CanvasLight, shadowElevation = 16.dp) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(T("family.addMemberTitle"), style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(16.dp))
                OutlinedTextField(
                    value = name, onValueChange = { name = it },
                    label = { Text(T("family.nameLabel")) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp)
                )
                Spacer(Modifier.height(12.dp))
                Text(T("family.relationshipLabel"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                Spacer(Modifier.height(4.dp))
                Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    relationships.chunked(4).forEach { rowRels ->
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            rowRels.forEach { rel ->
                                Surface(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(8.dp)),
                                    shape = RoundedCornerShape(8.dp),
                                    color = if (relationship == rel) PrimaryGreen else SurfaceLight,
                                    onClick = { relationship = rel }
                                ) {
                                    Text(
                                        rel,
                                        modifier = Modifier.padding(vertical = 8.dp),
                                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                                        color = if (relationship == rel) CanvasLight else TextPrimaryLight,
                                        textAlign = TextAlign.Center
                                    )
                                }
                            }
                            if (rowRels.size < 4) {
                                Spacer(Modifier.weight((4 - rowRels.size).toFloat()))
                            }
                        }
                    }
                }
                Spacer(Modifier.height(20.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    CcButton(onClick = onDismiss, variant = CcButtonVariant.Outline, modifier = Modifier.weight(1f)) {
                        Text(T("family.cancel"))
                    }
                    CcButton(onClick = { if (name.isNotBlank()) onAdd(name, relationship) }, modifier = Modifier.weight(1f)) {
                        Text(T("family.addBtn"))
                    }
                }
            }
        }
    }
}

@Composable
private fun CheckInOthersDialog(
    familyList: List<FamilyMember>,
    onDismiss: () -> Unit,
    onConfirm: (List<String>) -> Unit
) {
    var selectedIds by remember { mutableStateOf(setOf<String>()) }

    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = RoundedCornerShape(24.dp), color = CanvasLight, shadowElevation = 16.dp) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(T("family.checkInSomeoneWithMe"), style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(8.dp))
                Text(T("family.selectMembers"), style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                Spacer(Modifier.height(12.dp))

                familyList.forEach { member ->
                    val isSelected = selectedIds.contains(member.id)
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 3.dp)
                            .clip(RoundedCornerShape(10.dp)),
                        shape = RoundedCornerShape(10.dp),
                        color = if (isSelected) PrimaryGreen.copy(alpha = 0.1f) else SurfaceLight,
                        onClick = {
                            selectedIds = if (isSelected) selectedIds - member.id else selectedIds + member.id
                        }
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Checkbox(
                                checked = isSelected,
                                onCheckedChange = { checked ->
                                    selectedIds = if (checked) selectedIds + member.id else selectedIds - member.id
                                },
                                colors = CheckboxDefaults.colors(checkedColor = PrimaryGreen)
                            )
                            Spacer(Modifier.width(8.dp))
                            Column {
                                Text(member.name, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold)
                                Text(member.relationship, style = MaterialTheme.typography.labelSmall, color = TextSecondaryLight)
                            }
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))
                CcButton(
                    onClick = { onConfirm(selectedIds.toList()) },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = selectedIds.isNotEmpty()
                ) {
                    Text(T("family.confirmSafeCount").replace("{count}", selectedIds.size.toString()))
                }
            }
        }
    }
}

@Composable
private fun ReportSomeoneDialog(onDismiss: () -> Unit, onConfirm: (String) -> Unit) {
    var name by remember { mutableStateOf("") }
    var location by remember { mutableStateOf("") }
    var confirmed by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = onDismiss) {
        Surface(shape = RoundedCornerShape(24.dp), color = CanvasLight, shadowElevation = 16.dp, modifier = Modifier.padding(16.dp)) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Favorite, null, tint = PrimaryGreen, modifier = Modifier.size(24.dp))
                    Spacer(Modifier.width(8.dp))
                    Text(T("family.reportSomeoneTitle"), style = MaterialTheme.typography.titleMedium)
                }
                Spacer(Modifier.height(16.dp))

                OutlinedTextField(
                    value = name, onValueChange = { name = it },
                    label = { Text(T("family.personNameOpt")) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp)
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = location, onValueChange = { location = it },
                    label = { Text(T("family.locationLabel")) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp)
                )
                Spacer(Modifier.height(12.dp))
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp)),
                    shape = RoundedCornerShape(10.dp),
                    color = PrimaryGreen.copy(alpha = 0.1f)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Checkbox(
                            checked = confirmed,
                            onCheckedChange = { confirmed = it },
                            colors = CheckboxDefaults.colors(checkedColor = PrimaryGreen)
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(T("family.confirmNotice"), style = MaterialTheme.typography.bodySmall)
                    }
                }

                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    CcButton(onClick = onDismiss, variant = CcButtonVariant.Outline, modifier = Modifier.weight(1f)) {
                        Text(T("family.cancel"))
                    }
                    CcButton(onClick = { onConfirm(name) }, modifier = Modifier.weight(1f), enabled = confirmed) {
                        Text(T("family.confirmBtn"))
                    }
                }
            }
        }
    }
}
