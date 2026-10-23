package com.crisiscore.app.ui.screens.auth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.CloudDone
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.crisiscore.app.data.repository.CrisisCoreRepository
import com.crisiscore.app.ui.components.*
import com.crisiscore.app.ui.theme.*
import com.crisiscore.app.util.T
import kotlinx.coroutines.launch

@Composable
fun AuthScreen(
    repository: CrisisCoreRepository,
    onLoginSuccess: () -> Unit,
    onDismiss: (() -> Unit)? = null
) {
    var isLogin by remember { mutableStateOf(true) }
    var usernameOrPhone by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var selectedRole by remember { mutableStateOf("citizen") }
    var showPassword by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var loadingMessage by remember { mutableStateOf("Verifying with Render cloud backend...") }
    var error by remember { mutableStateOf<String?>(null) }
    var infoMessage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun validateInputs(): Boolean {
        error = null
        infoMessage = null
        val cleanIdentifier = usernameOrPhone.trim()

        if (cleanIdentifier.isEmpty()) {
            error = "Please enter your username or phone number"
            return false
        }

        if (isLogin) {
            if (password.isEmpty()) {
                error = "Please enter your password"
                return false
            }
        } else {
            if (name.trim().length < 2) {
                error = "Please enter your full name (at least 2 characters)"
                return false
            }
            if (cleanIdentifier.length < 10 || cleanIdentifier.length > 15) {
                error = "Username or phone must be between 10 and 15 characters"
                return false
            }
            if (password.length < 6) {
                error = "Password must be at least 6 characters"
                return false
            }
        }
        return true
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .statusBarsPadding()
                .padding(horizontal = 24.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Dismiss button if provided
            if (onDismiss != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End
                ) {
                    IconButton(
                        onClick = onDismiss,
                        modifier = Modifier
                            .size(36.dp)
                            .clip(CircleShape)
                            .background(SurfaceLight)
                    ) {
                        Icon(
                            Icons.Outlined.Close,
                            contentDescription = "Close",
                            tint = TextSecondaryLight,
                            modifier = Modifier.size(20.dp)
                        )
                    }
                }
            } else {
                Spacer(Modifier.height(16.dp))
            }

            // Shield Logo
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(RoundedCornerShape(18.dp))
                    .background(PrimaryGreen),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Filled.Shield, null, tint = CanvasLight, modifier = Modifier.size(36.dp))
            }
            Spacer(Modifier.height(12.dp))
            Text(
                T("app.name"),
                style = MaterialTheme.typography.headlineMedium.copy(fontWeight = FontWeight.Black),
                letterSpacing = 3.sp
            )
            Text(
                T("nav.subtitle"),
                style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                color = TextSecondaryLight
            )

            Spacer(Modifier.height(14.dp))

            // Render Backend connection pill
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = PrimaryGreen.copy(alpha = 0.08f),
                border = androidx.compose.foundation.BorderStroke(1.dp, PrimaryGreen.copy(alpha = 0.25f))
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF22C55E))
                    )
                    Spacer(Modifier.width(6.dp))
                    Icon(
                        Icons.Outlined.CloudDone,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp),
                        tint = PrimaryGreen
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(
                        "Render Backend: samvedna-sih2026-1.onrender.com",
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Bold),
                        color = PrimaryGreen
                    )
                }
            }

            Spacer(Modifier.height(28.dp))

            // Screen Mode Title
            Text(
                if (isLogin) "SIGN IN TO CRISISCORE" else "CREATE AN ACCOUNT",
                style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Bold),
                color = TextPrimaryLight
            )
            Text(
                if (isLogin)
                    "Enter your username/phone and password to verify with Render cloud"
                else
                    "Register a new account verified on the Render disaster network",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondaryLight,
                modifier = Modifier.padding(top = 4.dp, bottom = 20.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )

            // Name field (registration only)
            if (!isLogin) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Full Name") },
                    placeholder = { Text("e.g. Aryan Chavan") },
                    leadingIcon = { Icon(Icons.Filled.Person, null, modifier = Modifier.size(20.dp), tint = PrimaryGreen) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = PrimaryGreen,
                        unfocusedBorderColor = BorderLight,
                        focusedContainerColor = MaterialTheme.colorScheme.surface,
                        unfocusedContainerColor = MaterialTheme.colorScheme.surface
                    )
                )
                Spacer(Modifier.height(14.dp))

                // Role Selector for Swagger permission distinction
                Column(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        "SELECT ACCOUNT ROLE & PERMISSIONS",
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp, fontWeight = FontWeight.Black),
                        color = TextSecondaryLight
                    )
                    Spacer(Modifier.height(6.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        // Citizen role card
                        val isCitizen = selectedRole == "citizen"
                        Surface(
                            onClick = { selectedRole = "citizen" },
                            shape = RoundedCornerShape(12.dp),
                            color = if (isCitizen) PrimaryGreen.copy(alpha = 0.12f) else MaterialTheme.colorScheme.surface,
                            border = androidx.compose.foundation.BorderStroke(
                                width = if (isCitizen) 2.dp else 1.dp,
                                color = if (isCitizen) PrimaryGreen else BorderLight.copy(alpha = 0.5f)
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Column(modifier = Modifier.padding(10.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        Icons.Filled.Person,
                                        contentDescription = null,
                                        tint = if (isCitizen) PrimaryGreen else TextSecondaryLight,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(Modifier.width(6.dp))
                                    Text(
                                        "Citizen",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        color = if (isCitizen) PrimaryGreen else TextPrimaryLight
                                    )
                                }
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    "Community alerts, SOS reports & family tracking",
                                    fontSize = 9.sp,
                                    lineHeight = 11.sp,
                                    color = TextSecondaryLight
                                )
                            }
                        }

                        // Admin role card
                        val isAdmin = selectedRole == "admin"
                        Surface(
                            onClick = { selectedRole = "admin" },
                            shape = RoundedCornerShape(12.dp),
                            color = if (isAdmin) EmergencyRed.copy(alpha = 0.12f) else MaterialTheme.colorScheme.surface,
                            border = androidx.compose.foundation.BorderStroke(
                                width = if (isAdmin) 2.dp else 1.dp,
                                color = if (isAdmin) EmergencyRed else BorderLight.copy(alpha = 0.5f)
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Column(modifier = Modifier.padding(10.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        Icons.Filled.AdminPanelSettings,
                                        contentDescription = null,
                                        tint = if (isAdmin) EmergencyRed else TextSecondaryLight,
                                        modifier = Modifier.size(16.dp)
                                    )
                                    Spacer(Modifier.width(6.dp))
                                    Text(
                                        "Admin",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        color = if (isAdmin) EmergencyRed else TextPrimaryLight
                                    )
                                }
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    "Command clearance: verify incidents & audit logs",
                                    fontSize = 9.sp,
                                    lineHeight = 11.sp,
                                    color = TextSecondaryLight
                                )
                            }
                        }
                    }
                }
                Spacer(Modifier.height(14.dp))
            }

            // Username / Phone field
            OutlinedTextField(
                value = usernameOrPhone,
                onValueChange = { usernameOrPhone = it },
                label = { Text("Username or Phone Number") },
                placeholder = { Text(if (isLogin) "e.g. user_rick123 or 9876543210" else "10-15 characters username/phone") },
                leadingIcon = { Icon(Icons.Filled.AccountCircle, null, modifier = Modifier.size(20.dp), tint = PrimaryGreen) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(12.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = PrimaryGreen,
                    unfocusedBorderColor = BorderLight,
                    focusedContainerColor = SurfaceLight,
                    unfocusedContainerColor = SurfaceLight
                )
            )

            if (!isLogin) {
                Text(
                    "Must be 10–15 characters (e.g. 10-digit mobile number or unique username)",
                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                    color = TextSecondaryLight,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 8.dp, top = 4.dp)
                )
            }

            Spacer(Modifier.height(12.dp))

            // Password field
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Password") },
                placeholder = { Text("Enter your password") },
                leadingIcon = { Icon(Icons.Filled.Lock, null, modifier = Modifier.size(20.dp), tint = PrimaryGreen) },
                trailingIcon = {
                    IconButton(onClick = { showPassword = !showPassword }) {
                        Icon(
                            if (showPassword) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                            contentDescription = if (showPassword) "Hide password" else "Show password",
                            modifier = Modifier.size(20.dp),
                            tint = TextSecondaryLight
                        )
                    }
                },
                visualTransformation = if (showPassword) VisualTransformation.None else PasswordVisualTransformation(),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                shape = RoundedCornerShape(12.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = PrimaryGreen,
                    unfocusedBorderColor = BorderLight,
                    focusedContainerColor = SurfaceLight,
                    unfocusedContainerColor = SurfaceLight
                )
            )

            if (!isLogin) {
                Text(
                    "Minimum 6 characters",
                    style = MaterialTheme.typography.labelSmall.copy(fontSize = 10.sp),
                    color = TextSecondaryLight,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 8.dp, top = 4.dp)
                )
            }

            // Info message banner
            if (infoMessage != null) {
                Spacer(Modifier.height(12.dp))
                Surface(
                    shape = RoundedCornerShape(10.dp),
                    color = PrimaryGreen.copy(alpha = 0.12f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, PrimaryGreen.copy(alpha = 0.3f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Filled.CheckCircle, null, tint = PrimaryGreen, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(infoMessage!!, color = PrimaryGreen, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }

            // Error banner
            if (error != null) {
                Spacer(Modifier.height(12.dp))
                Surface(
                    shape = RoundedCornerShape(10.dp),
                    color = EmergencyRed.copy(alpha = 0.1f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, EmergencyRed.copy(alpha = 0.3f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Filled.ErrorOutline, null, tint = EmergencyRed, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(error!!, color = EmergencyRed, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }

            // Loading state details
            if (isLoading) {
                Spacer(Modifier.height(14.dp))
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(SurfaceLight, RoundedCornerShape(12.dp))
                        .padding(12.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = PrimaryGreen,
                        strokeWidth = 2.5.dp
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        loadingMessage,
                        style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Medium),
                        color = TextPrimaryLight
                    )
                    Text(
                        "If the Render server is waking from idle, please allow up to 30s.",
                        style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp),
                        color = TextSecondaryLight
                    )
                }
            }

            Spacer(Modifier.height(20.dp))

            // Main Action Button (Sign In / Create Account)
            CcButton(
                onClick = {
                    if (!validateInputs()) return@CcButton
                    isLoading = true
                    loadingMessage = if (isLogin) "Verifying credentials with Render cloud..." else "Registering account on Render backend..."
                    error = null
                    infoMessage = null

                    scope.launch {
                        val cleanIdentifier = usernameOrPhone.trim()
                        if (isLogin) {
                            val result = repository.login(cleanIdentifier, password)
                            isLoading = false
                            if (result.isSuccess) {
                                onLoginSuccess()
                            } else {
                                error = result.exceptionOrNull()?.message ?: "Login failed. Check username and password."
                            }
                        } else {
                            val regResult = repository.register(cleanIdentifier, password, name.trim(), selectedRole)
                            if (regResult.isSuccess) {
                                loadingMessage = "Account created! Signing in..."
                                val loginResult = repository.login(cleanIdentifier, password)
                                isLoading = false
                                if (loginResult.isSuccess) {
                                    onLoginSuccess()
                                } else {
                                    isLogin = true
                                    infoMessage = "Account created successfully as ${selectedRole.uppercase()}! Please sign in with your password."
                                }
                            } else {
                                isLoading = false
                                error = regResult.exceptionOrNull()?.message ?: "Registration failed."
                            }
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !isLoading && usernameOrPhone.isNotBlank() && password.isNotBlank()
            ) {
                Icon(
                    if (isLogin) Icons.Filled.Login else Icons.Filled.PersonAdd,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(if (isLogin) "SIGN IN WITH RENDER" else "CREATE ACCOUNT ON RENDER")
            }

            Spacer(Modifier.height(16.dp))

            // Swagger Verified Accounts Quick Test
            Surface(
                shape = RoundedCornerShape(12.dp),
                color = MaterialTheme.colorScheme.surface,
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderLight.copy(alpha = 0.5f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "SWAGGER VERIFIED ACCOUNTS",
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp, fontWeight = FontWeight.Black),
                            color = TextSecondaryLight
                        )
                        Text(
                            "DIFFERENT ROLES",
                            style = MaterialTheme.typography.labelSmall.copy(fontSize = 8.sp, fontWeight = FontWeight.Bold),
                            color = PrimaryGreen
                        )
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        // Citizen quick login
                        OutlinedButton(
                            onClick = {
                                isLogin = true
                                usernameOrPhone = "9999000002"
                                password = "CitizenPass123"
                                error = null
                                infoMessage = "Loaded Swagger Citizen account (9999000002)"
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 6.dp, vertical = 6.dp)
                        ) {
                            Icon(Icons.Filled.Person, null, modifier = Modifier.size(14.dp), tint = PrimaryGreen)
                            Spacer(Modifier.width(4.dp))
                            Text("Citizen Account", fontSize = 11.sp, maxLines = 1)
                        }

                        // Admin quick login
                        OutlinedButton(
                            onClick = {
                                isLogin = true
                                usernameOrPhone = "9999000001"
                                password = "AdminPass123"
                                error = null
                                infoMessage = "Loaded Swagger Admin account (9999000001)"
                            },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 6.dp, vertical = 6.dp)
                        ) {
                            Icon(Icons.Filled.AdminPanelSettings, null, modifier = Modifier.size(14.dp), tint = EmergencyRed)
                            Spacer(Modifier.width(4.dp))
                            Text("Admin Account", fontSize = 11.sp, maxLines = 1)
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // Switch between Login and Register
            TextButton(
                onClick = {
                    isLogin = !isLogin
                    error = null
                    infoMessage = null
                }
            ) {
                Text(
                    if (isLogin) "Don't have an account? " else "Already have an account? ",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondaryLight
                )
                Text(
                    if (isLogin) "Create Account" else "Sign In",
                    style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                    color = PrimaryGreen
                )
            }
        }
    }
}
