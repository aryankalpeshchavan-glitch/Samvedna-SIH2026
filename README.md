# CrisisCore Android (User Portal)

Native Android application for the CrisisCore disaster management platform — citizen-facing early warning, incident reporting, and emergency response coordination for landslide-prone regions of North Eastern India.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Kotlin 2.1 |
| UI | Jetpack Compose (Material3) |
| Architecture | MVVM (ViewModel + Repository + Retrofit) |
| Navigation | Jetpack Navigation Compose |
| Networking | Retrofit + OkHttp + Kotlinx Serialization |
| Offline | Room Database |
| Location | Google Play Services Location |
| Map | MapLibre GL Native |
| QR Scanning | ML Kit Barcode + CameraX |
| Build | Gradle Kotlin DSL, AGP 8.7 |

## Project Structure

```
app/src/main/java/com/crisiscore/app/
├── CrisisCoreApp.kt              # Application class (DI init)
├── MainActivity.kt               # Entry point
├── data/
│   ├── api/
│   │   ├── CrisisCoreApi.kt      # Retrofit API interface
│   │   └── RetrofitClient.kt     # Singleton Retrofit + auth token
│   ├── local/
│   │   └── OfflineDatabase.kt    # Room DB for offline SOS/incidents
│   ├── model/
│   │   └── Models.kt            # All data classes, enums, API models
│   └── repository/
│       └── CrisisCoreRepository.kt  # Data access facade
├── ui/
│   ├── components/
│   │   ├── AppHeader.kt          # Top app bar with language selector
│   │   ├── BottomNavBar.kt       # 6-tab animated bottom navigation
│   │   ├── CcComponents.kt       # Reusable Button, Card, Badge, etc.
│   │   └── SosConfirmDialog.kt   # SOS confirmation modal
│   ├── navigation/
│   │   └── CrisisCoreNavHost.kt  # Tab-based navigation controller
│   ├── screens/
│   │   ├── alerts/AlertsScreen.kt
│   │   ├── auth/AuthScreen.kt
│   │   ├── family/FamilyScreen.kt
│   │   ├── help/HelpScreen.kt
│   │   ├── home/HomeScreen.kt
│   │   ├── incident/IncidentScreen.kt
│   │   └── status/StatusScreen.kt
│   └── theme/
│       ├── Color.kt              # Color palette
│       ├── Theme.kt              # Material3 theme (light/dark)
│       └── Type.kt               # Typography scale
└── util/
    └── LocaleManager.kt          # i18n (7 languages) + translations
```

## How to Run

1. Open `CrisisCoreAndroid/` in Android Studio Ladybug or later
2. Sync Gradle (auto-downloads dependencies)
3. Set run target to an emulator (API 26+) or physical device
4. Configure backend URL in `app/build.gradle.kts` → `buildConfigField`:
   - Default: `http://10.0.2.2:8001` (Android emulator localhost)
   - For physical device: use your machine's local IP
5. Run the app

## Environment Variables / API Keys

| Config | Location | Default | Purpose |
|---|---|---|---|
| `API_BASE_URL` | `app/build.gradle.kts` buildConfigField | `http://10.0.2.2:8001` | Backend REST API |
| `WS_BASE_URL` | `app/build.gradle.kts` buildConfigField | `ws://10.0.2.2:8001/ws/status` | WebSocket status feed |

No external API keys required for demo mode. The app auto-registers a demo citizen account on first launch.

## Supported Languages

English, Hindi, Assamese, Bengali, Manipuri, Mizo, Khasi

## Permissions

| Permission | Purpose |
|---|---|
| `INTERNET` | API communication |
| `ACCESS_FINE_LOCATION` | GPS for SOS/incident location |
| `CAMERA` | QR code scanning for responder verification |
| `CALL_PHONE` | Direct helpline dialing |
| `READ_MEDIA_IMAGES` | Photo attachment for incident reports |

## Offline Support

Room database persists SOS and incident reports when offline. Data syncs automatically when connectivity is restored.
