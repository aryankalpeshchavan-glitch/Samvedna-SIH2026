package com.crisiscore.app.ui.screens.auth

import androidx.compose.foundation.background
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
    onLoginSuccess: () -> Unit
) {
    var isLogin by remember { mutableStateOf(true) }
    var phone by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }
    var showPassword by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun validateInputs(): Boolean {
        if (!isLogin && name.trim().length < 2) {
            error = "Please enter your full name"
            return false
        }
        val cleanPhone = phone.trim()
        if (cleanPhone.length < 10) {
            error = "Please enter a valid 10-digit phone number"
            return false
        }
        if (password.length < 6) {
            error = "Password must be at least 6 characters"
            return false
        }
        return true
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp, vertical = 48.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Logo
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
        Text(T("app.name"), style = MaterialTheme.typography.headlineMedium, letterSpacing = 4.sp)
        Text(T("nav.subtitle"), style = MaterialTheme.typography.labelSmall.copy(fontSize = 9.sp), color = TextSecondaryLight)

        Spacer(Modifier.height(36.dp))

        Text(
            if (isLogin) T("auth.loginTitle") else T("auth.registerTitle"),
            style = MaterialTheme.typography.titleLarge
        )

        Spacer(Modifier.height(20.dp))

        if (!isLogin) {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text(T("auth.nameLabel")) },
                leadingIcon = { Icon(Icons.Filled.Person, null, modifier = Modifier.size(20.dp)) },
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
            Spacer(Modifier.height(12.dp))
        }

        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            label = { Text(T("auth.phoneLabel")) },
            leadingIcon = { Icon(Icons.Filled.Phone, null, modifier = Modifier.size(20.dp)) },
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
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text(T("auth.passwordLabel")) },
            leadingIcon = { Icon(Icons.Filled.Lock, null, modifier = Modifier.size(20.dp)) },
            trailingIcon = {
                IconButton(onClick = { showPassword = !showPassword }) {
                    Icon(
                        if (showPassword) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                        null, modifier = Modifier.size(20.dp)
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

        if (error != null) {
            Spacer(Modifier.height(8.dp))
            Text(error!!, color = EmergencyRed, style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(20.dp))

        CcButton(
            onClick = {
                if (!validateInputs()) return@CcButton
                isLoading = true
                error = null
                scope.launch {
                    val formattedPhone = if (phone.startsWith("+")) phone.trim() else "+91${phone.trim()}"
                    if (isLogin) {
                        val token = repository.login(formattedPhone, password)
                        isLoading = false
                        if (token != null) {
                            onLoginSuccess()
                        } else {
                            error = "Invalid phone number or password"
                        }
                    } else {
                        val success = repository.register(formattedPhone, password, name.trim())
                        if (success) {
                            val token = repository.login(formattedPhone, password)
                            isLoading = false
                            if (token != null) {
                                onLoginSuccess()
                            } else {
                                isLogin = true
                                error = "Account registered successfully. Please sign in."
                            }
                        } else {
                            isLoading = false
                            error = "Registration failed. Try a different phone number."
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading && phone.isNotBlank() && password.isNotBlank()
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), color = CanvasLight, strokeWidth = 2.dp)
            } else {
                Text(if (isLogin) T("auth.loginButton") else T("auth.registerButton"))
            }
        }

        Spacer(Modifier.height(12.dp))

        CcButton(
            onClick = {
                isLoading = true
                error = null
                scope.launch {
                    val token = repository.autoLoginDemo()
                    isLoading = false
                    if (token != null) {
                        onLoginSuccess()
                    } else {
                        error = "Could not initialize demo session. Try again."
                    }
                }
            },
            variant = CcButtonVariant.Secondary,
            modifier = Modifier.fillMaxWidth(),
            enabled = !isLoading
        ) {
            Icon(Icons.Filled.PlayArrow, null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text(T("auth.demoButton"))
        }

        Spacer(Modifier.height(16.dp))

        TextButton(onClick = { isLogin = !isLogin }) {
            Text(
                if (isLogin) "${T("auth.noAccount")} " else "${T("auth.hasAccount")} ",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondaryLight
            )
            Text(
                if (isLogin) T("auth.registerButton") else T("auth.loginButton"),
                style = MaterialTheme.typography.bodySmall.copy(fontWeight = FontWeight.Bold),
                color = PrimaryGreen
            )
        }
    }
}
