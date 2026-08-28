import { WhyRiskStep, TerrainScanResult, SafeRouteInfo } from '../types/map';
import { CitizenMapReport } from '../types/emergency';

export const WHY_RISK_STEPS: WhyRiskStep[] = [
  {
    stepNumber: '01',
    title: 'HEAVY RAINFALL',
    value: '86 mm',
    unit: 'last 24 hours',
    description: 'Monsoon precipitation threshold surpassed regional 24h stability baseline.',
    statusColor: 'text-[#D88A32]',
  },
  {
    stepNumber: '02',
    title: 'SOIL MOISTURE',
    value: '78%',
    unit: 'pore-water saturation',
    description: 'Sub-surface soil saturation has reduced cohesion across upper clay layer.',
    statusColor: 'text-[#C6533C]',
  },
  {
    stepNumber: '03',
    title: 'TERRAIN SLOPE',
    value: '36°',
    unit: 'steep incline',
    description: 'Local topography exceeds critical 35° threshold for debris flow initiation.',
    statusColor: 'text-[#C6533C]',
  },
  {
    stepNumber: '04',
    title: 'HISTORICAL INCIDENTS',
    value: '3 Prior Events',
    unit: 'recorded in sector',
    description: 'Geospatial records indicate high recurrence interval during similar saturation.',
    statusColor: 'text-[#23483A]',
  },
  {
    stepNumber: '05',
    title: 'RISK ASSESSMENT',
    value: 'ELEVATED (WATCH)',
    unit: '72/100 index',
    description: 'High probability of localized slope instability along Sector 4 highway pass.',
    statusColor: 'text-[#8E2F2B]',
  },
];

export const MOCK_TERRAIN_SCAN: TerrainScanResult = {
  elevationMeters: 1420,
  slopeDegrees: 36,
  rainfall24hMm: 86,
  soilMoisturePct: 78,
  historicalIncidentCount: 3,
  riskScore: 72,
  riskCategory: 'WATCH',
  recommendation: 'Avoid unpaved mountain roads and monitor local evacuation advisories.',
};

export const MOCK_SAFE_ROUTE: SafeRouteInfo = {
  id: 'ROUTE-01',
  title: 'Sector 4 Evacuation Corridor',
  distanceKm: 2.4,
  estMinutes: 14,
  shelterName: 'High-Ground Community Shelter B',
  shelterCapacity: 450,
  shelterOccupancyPct: 38,
  blockedRoads: ['NH-10 Sector 4 Pass', 'Bridge Causeway 2'],
  safePathCoords: [
    [91.7362, 26.1445],
    [91.7420, 26.1490],
    [91.7480, 26.1530],
    [91.7540, 26.1580],
    [91.7610, 26.1620],
  ],
};

export const CITIZEN_MAP_REPORTS: CitizenMapReport[] = [
  {
    id: 'REP-101',
    category: 'ROAD_BLOCKED',
    title: 'NH-10 Mudslide Blockage',
    locationName: 'Sector 4 Pass, Assam',
    lat: 26.1485,
    lng: 91.7420,
    severity: 'HIGH',
    reportedTimeAgo: '18 mins ago',
    verifiedStatus: 'VERIFIED',
    description: 'Heavy mud flow blocking both lanes. Vehicles queued up.',
  },
  {
    id: 'REP-102',
    category: 'SLOPE_CRACK',
    title: 'Visible 2-inch Soil Fissure',
    locationName: 'Shillong Ridge Sector B',
    lat: 25.5788,
    lng: 91.8933,
    severity: 'WATCH',
    reportedTimeAgo: '42 mins ago',
    verifiedStatus: 'INVESTIGATING',
    description: 'Fissure extending 15 meters along the hill slope above residential area.',
  },
  {
    id: 'REP-103',
    category: 'FLOOD',
    title: 'River Causeway Overflow',
    locationName: 'Periyar Sub-Basin',
    lat: 25.2630,
    lng: 91.7320,
    severity: 'CRITICAL',
    reportedTimeAgo: '8 mins ago',
    verifiedStatus: 'VERIFIED',
    description: 'Water flowing 0.5m over main causeway. Inaccessible for light vehicles.',
  },
  {
    id: 'REP-104',
    category: 'LANDSLIDE',
    title: 'Debris Flow on East Cut',
    locationName: 'Itanagar Bypass',
    lat: 27.0844,
    lng: 93.6053,
    severity: 'CRITICAL',
    reportedTimeAgo: '25 mins ago',
    verifiedStatus: 'VERIFIED',
    description: 'Boulders and tree debris fallen across mountain pass.',
  },
];

export const STORY_MODE_SLIDES = [
  {
    id: 1,
    title: 'THE NORTHEAST TERRAIN',
    subtitle: 'High Precipitation & Steep Topography',
    description: 'The North Eastern Region of India features steep mountain slopes and intense monsoon rainfall, making it exceptionally vulnerable to landslide hazards.',
  },
  {
    id: 2,
    title: 'RAINFALL ACCUMULATION',
    subtitle: 'Breaching 24h Thresholds',
    description: 'Heavy precipitation saturates upper soil layers, increasing pore-water pressure and weight on vulnerable slope faces.',
  },
  {
    id: 3,
    title: 'SLOPE STABILITY MODEL',
    subtitle: 'Geospatial AI Risk Calculation',
    description: 'CrisisCore combines elevation, slope angles (>35°), soil moisture, and historical occurrence into an immediate hazard assessment.',
  },
  {
    id: 4,
    title: 'CITIZEN DECISION LAYER',
    subtitle: 'Actionable Early Warning',
    description: 'Citizens receive clear warnings ("Why is my area at risk?"), safe evacuation routes, and offline emergency request capabilities.',
  },
];
