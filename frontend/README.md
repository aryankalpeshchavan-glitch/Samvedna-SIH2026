# CrisisCore — Citizen Emergency Frontend (`/frontend-citizen`)

> **Last-mile AI decision + action layer for landslide, flash-flood, and multi-hazard emergencies.**  
> *SIH26001 — AI-Based Early Warning and Landslide Risk Monitoring System in the North Eastern Region of India*

---

## 1. Editorial Cartographic Visual Direction

The visual identity is modeled after **environmental research cartography, National Geographic publications, and cinematic editorial design**.

- **Background Canvas**: Warm Paper `#F4F1E8`
- **Secondary Surface**: Mist `#E8E6DC` & Bone `#FAF9F3`
- **Typography**: `Space Grotesk` (Headings), `Inter` (Body), `Instrument Serif` (Editorial Accents)
- **Palette**: Forest Green (`#23483A`), Clay (`#A87C58`), Sand (`#C7B89B`), Charcoal (`#202622`), Saffron (`#D88A32`), Vermilion (`#C6533C`), Deep Red (`#8E2F2B`). Zero neon, zero glow, zero cyberpunk black.

---

## 2. "The Map is the Product" (90% Hero Viewport)

- The 3D map dominates **85–95% of the starting viewport**.
- Cartographic MapLibre GL JS engine with 3D DEM Terrarium elevation relief, warm hillshading, topographic contour lines, and warm state fill overlays.
- Minimal top navigation bar (`CRISISCORE`, `MAP`, `REPORT`, `SOS`, `FAMILY`, `ALERTS`, `LANGUAGE`).
- Floating paper overlay controls (`MY AREA`, `WHY IS MY AREA AT RISK?`, `SCAN TERRAIN`, `SHOW SAFE ROUTE`, `STORY MODE`).

---

## 3. Interactive Feature Matrix

| Feature | Description | Implementation Details |
| :--- | :--- | :--- |
| **"Why Is My Area at Risk?"** | 5-step visual explainer of risk drivers | Staggered Anime.js steps (*Rainfall → Soil Moisture → Terrain Slope → Historical → Risk Assessment*) |
| **"Scan Terrain"** | Environmental topography scan | Animated scanning line computing cartographic **Risk Index: 72/100** |
| **"Show Safe Route"** | Animated evacuation path | Draws safe corridor across 3D terrain to nearest Community Shelter |
| **Story Mode** | SIH presentation narrative | 4-stage guided presentation mode for SIH judges |
| **Community Map Layer** | Citizen field observations | Interactive citizen report pins mapped directly to coordinates |
| **SOS Action Control** | Restrained emergency action | Clean `SOS — Get Help` vermilion button with hold-to-confirm modal |
| **3-Tier Alerts & Audio** | Multilingual public safety alerts | Public safety notices + Web Speech API TTS audio broadcasting |
| **Offline Storage** | IndexedDB offline persistence | Queueing pending SOS requests in browser `idb` database when offline |

---

## 4. How to Run

```bash
# 1. Install dependencies
npm install

# 2. Launch dev server
npm run dev

# 3. Production build & type check
npm run build
```
