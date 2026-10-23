package com.crisiscore.app.ui.screens.help

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.model.Helpline
import com.crisiscore.app.data.model.HelplineColorType
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.LocaleManager
import com.crisiscore.app.util.T
import com.crisiscore.app.util.TtsManager

@Composable
fun HelpScreen() {
    val context = LocalContext.current
    var selectedCategory by remember { mutableStateOf("All") }
    var searchQuery by remember { mutableStateOf("") }

    val categories = remember {
        listOf("All", "Disaster", "Medical & Fire", "Security", "Social & Support")
    }

    val helplines = remember {
        listOf(
            Helpline(
                title = "112 National Emergency",
                number = "112",
                altNumber = "100",
                description = "Unified Pan-India 24x7 Emergency for Police, Fire, Ambulance & SDRF. Works without SIM or signal lock.",
                badge = "24x7 ALL-IN-ONE",
                colorType = HelplineColorType.RED,
                category = "Emergency"
            ),
            Helpline(
                title = "NDRF National Disaster Helpline",
                number = "1078",
                altNumber = "+91 11 26701728",
                description = "National Disaster Response Force HQ 24x7 Control Room for flood, landslide & building rescue dispatch.",
                badge = "DISASTER HQ",
                colorType = HelplineColorType.RED,
                category = "Disaster"
            ),
            Helpline(
                title = "State Disaster Management (SEOC)",
                number = "1070",
                altNumber = "+91 361 2237221",
                description = "State Emergency Operation Centre (Assam & North East). Evacuation orders, shelter allocation & relief.",
                badge = "STATE SEOC",
                colorType = HelplineColorType.GREEN,
                category = "Disaster"
            ),
            Helpline(
                title = "District Control Room (DEOC)",
                number = "1077",
                altNumber = "+91 361 2237011",
                description = "District Magistrate / DC Disaster Emergency Cell for localized relief, supplies and flood assistance.",
                badge = "DISTRICT DEOC",
                colorType = HelplineColorType.GREEN,
                category = "Disaster"
            ),
            Helpline(
                title = "Emergency Ambulance & EMS",
                number = "108",
                altNumber = "102",
                description = "24x7 Critical Care Ambulance, trauma resuscitation & hospital transit. 102 for maternity & infant emergency.",
                badge = "CRITICAL EMS",
                colorType = HelplineColorType.RED,
                category = "Medical & Fire"
            ),
            Helpline(
                title = "Fire & Rescue Services",
                number = "101",
                altNumber = "+91 361 2540101",
                description = "Emergency fire breakout dispatch, hazmat containment, chemical spills and collapsed structural rescue.",
                badge = "FIRE & RESCUE",
                colorType = HelplineColorType.AMBER,
                category = "Medical & Fire"
            ),
            Helpline(
                title = "Police Control Room",
                number = "100",
                altNumber = "112",
                description = "Law enforcement, riot control, roadblock reporting, evacuation perimeter security and escort.",
                badge = "POLICE 24/7",
                colorType = HelplineColorType.GREEN,
                category = "Security"
            ),
            Helpline(
                title = "Women in Distress Helpline",
                number = "1091",
                altNumber = "181",
                description = "National Commission for Women (NCW) & state 24x7 emergency response for women safety and rescue.",
                badge = "WOMEN SAFETY",
                colorType = HelplineColorType.AMBER,
                category = "Social & Support"
            ),
            Helpline(
                title = "Childline Emergency Support",
                number = "1098",
                altNumber = "+91 22 23881098",
                description = "24-hour free emergency service for separated, lost, or stranded children in disaster-hit zones.",
                badge = "CHILD RESCUE",
                colorType = HelplineColorType.AMBER,
                category = "Social & Support"
            ),
            Helpline(
                title = "Senior Citizen Helpline (Elder Line)",
                number = "14567",
                altNumber = "1800 180 1253",
                description = "Ministry of Social Justice 24x7 emergency rescue, medication dispatch and shelter for elderly citizens.",
                badge = "ELDER LINE",
                colorType = HelplineColorType.GREEN,
                category = "Social & Support"
            ),
            Helpline(
                title = "Tele-MANAS Mental Health Distress",
                number = "14416",
                altNumber = "1800 891 4416",
                description = "24x7 toll-free crisis counseling and trauma support in 20+ Indian languages for disaster survivors.",
                badge = "TRAUMA SUPPORT",
                colorType = HelplineColorType.GREEN,
                category = "Medical & Fire"
            ),
            Helpline(
                title = "National Highway Accident & Patrol",
                number = "1033",
                altNumber = "+91 11 25074100",
                description = "NHAI 24x7 road accidents, highway crane assistance, debris clearance and route blockade clearing.",
                badge = "HIGHWAY AID",
                colorType = HelplineColorType.AMBER,
                category = "Medical & Fire"
            ),
            Helpline(
                title = "Cyber Crime Emergency Helpline",
                number = "1930",
                altNumber = "155260",
                description = "Ministry of Home Affairs immediate incident reporting & financial fraud lien freezing.",
                badge = "CYBER CRIME",
                colorType = HelplineColorType.GREEN,
                category = "Security"
            ),
            Helpline(
                title = "Rail Madad Railway Emergency",
                number = "139",
                altNumber = "+91 11 23386000",
                description = "Indian Railways security, medical emergencies on trains/tracks and derailment assistance.",
                badge = "RAIL RESCUE",
                colorType = HelplineColorType.AMBER,
                category = "Security"
            ),
            Helpline(
                title = "Red Cross Blood Bank & Relief",
                number = "1910",
                altNumber = "+91 11 23716441",
                description = "Indian Red Cross Society emergency blood units, first-aid camp coordination and disaster blankets.",
                badge = "BLOOD & AID",
                colorType = HelplineColorType.RED,
                category = "Medical & Fire"
            )
        )
    }

    fun dial(phone: String) {
        val clean = phone.replace(" ", "").replace("-", "")
        val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$clean"))
        context.startActivity(intent)
    }

    val filteredHelplines = remember(selectedCategory, searchQuery) {
        helplines.filter { h ->
            val matchesCategory = when (selectedCategory) {
                "All" -> true
                "Disaster" -> h.category == "Disaster" || h.number in listOf("112", "1078", "1070", "1077")
                "Medical & Fire" -> h.category == "Medical & Fire" || h.number in listOf("108", "102", "101", "14416", "1910", "1033")
                "Security" -> h.category == "Security" || h.number in listOf("100", "112", "1930", "139")
                "Social & Support" -> h.category == "Social & Support" || h.number in listOf("1091", "1098", "14567")
                else -> true
            }
            val matchesSearch = if (searchQuery.isBlank()) true else {
                val q = searchQuery.trim().lowercase()
                h.title.lowercase().contains(q) ||
                h.number.contains(q) ||
                h.altNumber.contains(q) ||
                h.description.lowercase().contains(q) ||
                h.badge.lowercase().contains(q)
            }
            matchesCategory && matchesSearch
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 14.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        PageHeader(tag = T("help.categoryHeader"), title = T("help.title"))

        // Priority 112 Universal Emergency Banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = EmergencyRed,
            shadowElevation = 6.dp
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(RoundedCornerShape(12.dp))
                                .background(CanvasLight),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Filled.Emergency, contentDescription = null, tint = EmergencyRed, modifier = Modifier.size(24.dp))
                        }
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text(
                                "NATIONAL EMERGENCY 112",
                                style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Black),
                                color = CanvasLight,
                                letterSpacing = 1.sp
                            )
                            Text(
                                "Unified Police, Fire, Ambulance & Disaster Response",
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                                color = CanvasLight.copy(alpha = 0.85f)
                            )
                        }
                    }
                    Surface(
                        shape = RoundedCornerShape(6.dp),
                        color = CanvasLight.copy(alpha = 0.2f)
                    ) {
                        Text(
                            "PAN-INDIA 24x7",
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 3.dp),
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Bold),
                            color = CanvasLight
                        )
                    }
                }

                Spacer(Modifier.height(12.dp))

                Text(
                    "Works even without SIM or carrier lock. Automatically routes call to nearest emergency dispatch team.",
                    style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp),
                    color = CanvasLight.copy(alpha = 0.95f)
                )

                Spacer(Modifier.height(14.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(
                        onClick = { dial("112") },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = CanvasLight),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Filled.Phone, null, tint = EmergencyRed, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("DIAL 112 (FREE)", fontWeight = FontWeight.Black, fontSize = 12.sp, color = EmergencyRed)
                    }

                    OutlinedButton(
                        onClick = {
                            val smsIntent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:112")).apply {
                                putExtra("sms_body", "EMERGENCY SOS: Immediate rescue assistance required via Samvedna CrisisCore.")
                            }
                            context.startActivity(smsIntent)
                        },
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = CanvasLight),
                        border = androidx.compose.foundation.BorderStroke(1.5.dp, CanvasLight),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Filled.Sms, null, tint = CanvasLight, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("SOS SMS", fontWeight = FontWeight.Bold, fontSize = 11.sp, color = CanvasLight)
                    }
                }
            }
        }

        // Search Bar
        OutlinedTextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("Search 15+ helplines by name, service or number...") },
            leadingIcon = { Icon(Icons.Filled.Search, null, tint = PrimaryGreen, modifier = Modifier.size(20.dp)) },
            trailingIcon = {
                if (searchQuery.isNotEmpty()) {
                    IconButton(onClick = { searchQuery = "" }) {
                        Icon(Icons.Filled.Clear, null, modifier = Modifier.size(18.dp))
                    }
                }
            },
            shape = RoundedCornerShape(12.dp),
            singleLine = true,
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = PrimaryGreen,
                unfocusedBorderColor = BorderLight.copy(alpha = 0.6f),
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface
            )
        )

        // Category Filter Chips
        LazyRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(categories) { cat ->
                val isSelected = selectedCategory == cat
                Surface(
                    onClick = { selectedCategory = cat },
                    shape = RoundedCornerShape(10.dp),
                    color = if (isSelected) PrimaryGreen else MaterialTheme.colorScheme.surface,
                    border = androidx.compose.foundation.BorderStroke(
                        width = 1.dp,
                        color = if (isSelected) PrimaryGreen else BorderLight.copy(alpha = 0.5f)
                    )
                ) {
                    Text(
                        cat,
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                        style = MaterialTheme.typography.labelSmall.copy(
                            fontSize = 11.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium
                        ),
                        color = if (isSelected) CanvasLight else TextPrimaryLight
                    )
                }
            }
        }

        // Audio readout banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface,
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderLight.copy(alpha = 0.5f))
        ) {
            Row(
                modifier = Modifier.padding(14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(PrimaryGreen),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Filled.Headset, null, tint = CanvasLight, modifier = Modifier.size(24.dp))
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(T("help.subtitle"), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Text("Audio broadcast of all essential disaster helplines", style = MaterialTheme.typography.bodySmall, color = TextSecondaryLight)
                }
                IconButton(onClick = {
                    val speech = filteredHelplines.take(6).joinToString(". ") { "${it.title}: dial ${it.number}" }
                    TtsManager.speak(speech, LocaleManager.currentLanguage.value)
                }) {
                    Icon(Icons.Filled.VolumeUp, null, tint = PrimaryGreen, modifier = Modifier.size(22.dp))
                }
            }
        }

        // Helplines Count and Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "VERIFIED EMERGENCY HELPLINES (${filteredHelplines.size})",
                style = MaterialTheme.typography.labelSmall.copy(fontWeight = FontWeight.Black),
                color = PrimaryGreen
            )
            Text(
                "Toll-free 24/7",
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                color = TextSecondaryLight
            )
        }

        // Helplines List
        filteredHelplines.forEach { helpline ->
            HelplineCard(
                helpline = helpline,
                onCallPrimary = { dial(helpline.number) },
                onCallAlt = { dial(helpline.altNumber) }
            )
        }

        // Official Agency Headquarters Directory
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            backgroundColor = MapBackground
        ) {
            Text(T("help.agenciesHeader"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen, fontWeight = FontWeight.Black)
            Spacer(Modifier.height(10.dp))

            val agencies = listOf(
                Triple("NDRF 1st Bn HQ", "Patgaon, Guwahati", "+91 361 2840001"),
                Triple("SDRF Control Room", "Kahilipara, Assam", "+91 361 2237011"),
                Triple("MDoNER Relief HQ", "Vigyan Bhawan, Shillong", "+91 364 2522000"),
            )

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                agencies.forEach { (name, loc, phone) ->
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .clickable { dial(phone) },
                        shape = RoundedCornerShape(10.dp),
                        color = MaterialTheme.colorScheme.surface,
                        border = androidx.compose.foundation.BorderStroke(1.dp, BorderLight.copy(alpha = 0.5f))
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Text(name, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), fontWeight = FontWeight.Bold, color = TextPrimaryLight, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text(loc, style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight, maxLines = 1)
                            Text(phone, style = MaterialTheme.typography.bodySmall.copy(fontSize = 10.sp, fontWeight = FontWeight.Bold, color = PrimaryGreen), modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            }
        }

        // Survival Guidance
        Text(T("help.guidanceHeader"), style = MaterialTheme.typography.labelSmall, color = PrimaryGreen, fontWeight = FontWeight.Black)

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            GuidanceCard(T("help.landslideTitle"), EmergencyRed, T("help.landslideGuidance"), Modifier.weight(1f))
            GuidanceCard(T("help.floodTitle"), PrimaryGreen, T("help.floodGuidance"), Modifier.weight(1f))
            GuidanceCard(T("help.quakeTitle"), WarningAmber, T("help.quakeGuidance"), Modifier.weight(1f))
        }

        // Offline SMS Dispatch Notice
        CcCard(
            modifier = Modifier.fillMaxWidth(),
            borderColor = EmergencyRed.copy(alpha = 0.4f),
            backgroundColor = EmergencyRed.copy(alpha = 0.05f)
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Sms, null, tint = EmergencyRed, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(12.dp))
                Column {
                    Text(T("help.offlineTitle"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 11.sp), color = EmergencyRed, fontWeight = FontWeight.Black)
                    Spacer(Modifier.height(4.dp))
                    Text(T("help.offlineMessage"), style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), color = TextPrimaryLight)
                }
            }
        }

        Spacer(Modifier.height(80.dp))
    }
}

@Composable
private fun HelplineCard(
    helpline: Helpline,
    onCallPrimary: () -> Unit,
    onCallAlt: () -> Unit
) {
    val color = when (helpline.colorType) {
        HelplineColorType.RED -> EmergencyRed
        HelplineColorType.GREEN -> PrimaryGreen
        HelplineColorType.AMBER -> WarningAmber
    }

    CcCard(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.fillMaxWidth()) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(44.dp)
                        .clip(RoundedCornerShape(12.dp))
                        .background(color.copy(alpha = 0.12f)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        when (helpline.colorType) {
                            HelplineColorType.RED -> Icons.Filled.Warning
                            HelplineColorType.GREEN -> Icons.Filled.Headset
                            HelplineColorType.AMBER -> Icons.Filled.LocalFireDepartment
                        },
                        null, tint = color, modifier = Modifier.size(22.dp)
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            helpline.title,
                            style = MaterialTheme.typography.titleMedium.copy(fontSize = 14.sp, fontWeight = FontWeight.Bold),
                            color = TextPrimaryLight
                        )
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = color.copy(alpha = 0.12f)
                        ) {
                            Text(
                                helpline.badge,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Black),
                                color = color
                            )
                        }
                    }
                    Text(
                        helpline.description,
                        style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp),
                        color = TextSecondaryLight,
                        modifier = Modifier.padding(top = 2.dp),
                        lineHeight = 14.sp
                    )
                }
            }

            Spacer(Modifier.height(10.dp))

            // Action Call Buttons for Primary & Alternate Number
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Primary number button
                Button(
                    onClick = onCallPrimary,
                    modifier = Modifier.weight(1.2f),
                    colors = ButtonDefaults.buttonColors(containerColor = color),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Icon(Icons.Filled.Phone, null, modifier = Modifier.size(14.dp), tint = CanvasLight)
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "Call ${helpline.number}",
                        style = MaterialTheme.typography.labelMedium.copy(fontSize = 11.sp, fontWeight = FontWeight.Bold),
                        color = CanvasLight,
                        maxLines = 1
                    )
                }

                // Alternate number button
                if (helpline.altNumber.isNotBlank()) {
                    OutlinedButton(
                        onClick = onCallAlt,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = color),
                        border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.6f)),
                        shape = RoundedCornerShape(8.dp),
                        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 6.dp)
                    ) {
                        Icon(Icons.Outlined.PhoneForwarded, null, modifier = Modifier.size(12.dp), tint = color)
                        Spacer(Modifier.width(4.dp))
                        Text(
                            "Alt: ${helpline.altNumber}",
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp, fontWeight = FontWeight.SemiBold),
                            color = color,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun GuidanceCard(title: String, color: Color, text: String, modifier: Modifier = Modifier) {
    CcCard(modifier = modifier, borderColor = color.copy(alpha = 0.3f)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                when (color) {
                    EmergencyRed -> Icons.Filled.Warning
                    PrimaryGreen -> Icons.Filled.Water
                    else -> Icons.Filled.Landscape
                },
                null, tint = color, modifier = Modifier.size(14.dp)
            )
            Spacer(Modifier.width(6.dp))
            Text(title, style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = color, fontWeight = FontWeight.Black)
        }
        Spacer(Modifier.height(6.dp))
        Text(text, style = MaterialTheme.typography.bodySmall.copy(fontSize = 11.sp), color = TextPrimaryLight)
    }
}
