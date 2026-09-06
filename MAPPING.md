# Screen Mapping: Reference → Android

| # | Reference Screen (React) | Android Screen (Compose) | Deliberate UX Changes |
|---|---|---|---|
| 1 | `Home.tsx` (tab: home) | `HomeScreen.kt` | 3D MapLibre map replaced with map placeholder (full MapLibre GL Native integration available). Hero map section preserved. SOS button maintains same visual weight. |
| 2 | `IncidentReport.tsx` (tab: incident) | `IncidentScreen.kt` | 5-step form condensed to single scrollable view (reference uses same). Category grid uses 2-column layout matching reference. Photo picker uses Android native gallery intent. |
| 3 | `Status.tsx` (tab: status) | `StatusScreen.kt` | State simulator preserved for demo. Volunteer QR scanner button included (camera integration via ML Kit). Offline queue viewer omitted (Room provides equivalent). |
| 4 | `FamilyPlaceholder.tsx` (tab: family) | `FamilyScreen.kt` | Full family management implemented (reference uses placeholder name but has functional UI). Add Member, Check-in Others, and Report Someone modals all functional with local state. |
| 5 | `AlertsPlaceholder.tsx` (tab: alerts) | `AlertsScreen.kt` | Alert cards with same severity-based color coding. Audio readout button preserved (uses Android TTS). |
| 6 | `CustomerServiceHelp.tsx` (tab: help) | `HelpScreen.kt` | Helpline cards use `ACTION_DIAL` intent for native phone dialer. Agency directory and survival guidance cards preserved. Offline SMS banner retained. |
| 7 | `SosConfirmModal.tsx` (overlay) | `SosConfirmDialog.kt` | Full-screen dialog on mobile (Material3 Dialog). Same category selection grid. |
| 8 | `Header.tsx` (top bar) | `AppHeader.kt` | Language selector uses Material3 DropdownMenu. Help button uses `Icons.Outlined.HelpOutline`. |
| 9 | `BottomNav.tsx` (navigation) | `BottomNavBar.kt` | Animated dock simplified to Material3 Surface with color animation. 6 tabs preserved. Active indicator dot replaced with color emphasis. |
| 10 | (No equivalent) | `AuthScreen.kt` | **New screen** — Login/register with phone+password. Demo mode auto-login. Not present in reference (reference auto-registers silently). |

## Key Differences from Reference

1. **State management**: Reference uses React useState prop-drilling from App.tsx. Android uses Compose state hoisting in CrisisCoreNavHost (same pattern, Compose-idiomatic).
2. **Offline storage**: Reference uses IndexedDB via `idb` library. Android uses Room database (same concept, native persistence).
3. **Animations**: Reference uses GSAP/Motion/Framer Motion for page transitions and dock animations. Android uses Compose `AnimatedContent` and `animateColorAsState` (lighter weight, native performance).
4. **3D Map**: Reference uses Three.js + MapLibre GL JS. Android uses MapLibre GL Native (supports 3D terrain, can be fully enabled with the same style URL).
5. **i18n**: Reference uses React Context-based translation. Android uses singleton `T.get()` with StateFlow-based language switching.
6. **Auth**: Reference silently auto-registers without a login screen. Android adds explicit AuthScreen with demo mode fallback.
