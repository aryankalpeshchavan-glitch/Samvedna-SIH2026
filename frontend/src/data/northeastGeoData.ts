import { NeStateInfo, MonitoringPoint } from '../types/map';

// Reference center coordinates for Northeast India: Lat 26.2° N, Lng 92.5° E
export const NE_CENTER: [number, number] = [92.5, 26.2]; // [lng, lat] for MapLibre

export const NORTHEAST_STATES: NeStateInfo[] = [
  {
    id: 'assam',
    name: 'Assam',
    code: 'AS',
    capital: 'Dispur / Guwahati',
    riskLevel: 'HIGH',
    center: [26.2006, 92.9376],
    avgRainfall24h: 142.5,
    elevationRange: '50m - 1,200m',
    activeLandslideZones: 14,
    avgSoilMoisture: 78,
    heightOffset: 0.6,
    polygonCoords: [
      [
        [89.85, 26.10], [90.20, 26.65], [91.30, 26.85], [92.50, 26.90],
        [93.80, 27.35], [95.20, 27.75], [96.00, 27.60], [95.80, 26.95],
        [94.50, 26.60], [93.40, 26.15], [92.40, 25.80], [91.10, 25.95],
        [90.10, 25.85], [89.85, 26.10]
      ]
    ]
  },
  {
    id: 'arunachal',
    name: 'Arunachal Pradesh',
    code: 'AR',
    capital: 'Itanagar',
    riskLevel: 'CRITICAL',
    center: [28.2180, 94.7278],
    avgRainfall24h: 215.0,
    elevationRange: '300m - 7,000m',
    activeLandslideZones: 28,
    avgSoilMoisture: 88,
    heightOffset: 2.2,
    polygonCoords: [
      [
        [91.60, 27.30], [91.80, 27.95], [92.60, 28.50], [94.00, 29.10],
        [95.50, 29.40], [97.30, 28.40], [97.10, 27.60], [96.20, 27.15],
        [94.80, 27.20], [93.20, 27.10], [91.60, 27.30]
      ]
    ]
  },
  {
    id: 'meghalaya',
    name: 'Meghalaya',
    code: 'ML',
    capital: 'Shillong',
    riskLevel: 'CRITICAL',
    center: [25.4670, 91.3662],
    avgRainfall24h: 280.4,
    elevationRange: '150m - 1,965m',
    activeLandslideZones: 22,
    avgSoilMoisture: 92,
    heightOffset: 1.4,
    polygonCoords: [
      [
        [89.80, 25.20], [90.30, 25.90], [91.80, 25.85], [92.80, 25.25],
        [92.50, 25.05], [91.50, 25.10], [90.50, 25.15], [89.80, 25.20]
      ]
    ]
  },
  {
    id: 'sikkim',
    name: 'Sikkim',
    code: 'SK',
    capital: 'Gangtok',
    riskLevel: 'HIGH',
    center: [27.5330, 88.5122],
    avgRainfall24h: 168.2,
    elevationRange: '280m - 8,586m',
    activeLandslideZones: 19,
    avgSoilMoisture: 84,
    heightOffset: 2.8,
    polygonCoords: [
      [
        [88.05, 27.10], [88.15, 27.75], [88.75, 28.15], [88.90, 27.45],
        [88.65, 27.10], [88.05, 27.10]
      ]
    ]
  },
  {
    id: 'nagaland',
    name: 'Nagaland',
    code: 'NL',
    capital: 'Kohima',
    riskLevel: 'HIGH',
    center: [26.1584, 94.5624],
    avgRainfall24h: 135.0,
    elevationRange: '200m - 3,840m',
    activeLandslideZones: 12,
    avgSoilMoisture: 76,
    heightOffset: 1.6,
    polygonCoords: [
      [
        [93.30, 25.60], [93.80, 26.20], [94.80, 27.00], [95.20, 26.80],
        [94.40, 25.90], [93.70, 25.40], [93.30, 25.60]
      ]
    ]
  },
  {
    id: 'manipur',
    name: 'Manipur',
    code: 'MN',
    capital: 'Imphal',
    riskLevel: 'MEDIUM',
    center: [24.6637, 93.9063],
    avgRainfall24h: 98.4,
    elevationRange: '40m - 2,994m',
    activeLandslideZones: 8,
    avgSoilMoisture: 68,
    heightOffset: 1.3,
    polygonCoords: [
      [
        [93.00, 24.20], [93.15, 25.65], [94.50, 25.65], [94.75, 24.15],
        [93.85, 23.85], [93.00, 24.20]
      ]
    ]
  },
  {
    id: 'mizoram',
    name: 'Mizoram',
    code: 'MZ',
    capital: 'Aizawl',
    riskLevel: 'MEDIUM',
    center: [23.1645, 92.9376],
    avgRainfall24h: 112.0,
    elevationRange: '20m - 2,157m',
    activeLandslideZones: 9,
    avgSoilMoisture: 72,
    heightOffset: 1.2,
    polygonCoords: [
      [
        [92.30, 21.95], [92.15, 24.25], [93.15, 24.45], [93.40, 23.05],
        [92.80, 21.90], [92.30, 21.95]
      ]
    ]
  },
  {
    id: 'tripura',
    name: 'Tripura',
    code: 'TR',
    capital: 'Agartala',
    riskLevel: 'LOW',
    center: [23.9408, 91.9882],
    avgRainfall24h: 62.5,
    elevationRange: '15m - 939m',
    activeLandslideZones: 3,
    avgSoilMoisture: 58,
    heightOffset: 0.5,
    polygonCoords: [
      [
        [91.10, 23.00], [91.25, 24.50], [92.30, 24.40], [92.20, 23.70],
        [91.70, 22.90], [91.10, 23.00]
      ]
    ]
  }
];

export const MONITORING_POINTS: MonitoringPoint[] = [
  {
    id: 'ST-01',
    name: 'Guwahati Slope Node Alpha',
    stateId: 'assam',
    lat: 26.1445,
    lng: 91.7362,
    riskLevel: 'HIGH',
    rainfall24hMm: 154.2,
    soilMoisturePct: 82,
    slopeAngleDeg: 34,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '5 mins ago',
  },
  {
    id: 'ST-02',
    name: 'Itanagar Crest Station 4',
    stateId: 'arunachal',
    lat: 27.0844,
    lng: 93.6053,
    riskLevel: 'CRITICAL',
    rainfall24hMm: 228.6,
    soilMoisturePct: 94,
    slopeAngleDeg: 46,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '2 mins ago',
  },
  {
    id: 'ST-03',
    name: 'Cherrapunji High-Surge Station',
    stateId: 'meghalaya',
    lat: 25.2630,
    lng: 91.7320,
    riskLevel: 'CRITICAL',
    rainfall24hMm: 312.0,
    soilMoisturePct: 98,
    slopeAngleDeg: 42,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '1 min ago',
  },
  {
    id: 'ST-04',
    name: 'Shillong Ridge Radar-02',
    stateId: 'meghalaya',
    lat: 25.5788,
    lng: 91.8933,
    riskLevel: 'HIGH',
    rainfall24hMm: 186.4,
    soilMoisturePct: 88,
    slopeAngleDeg: 38,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '8 mins ago',
  },
  {
    id: 'ST-05',
    name: 'Gangtok High-Pass Node',
    stateId: 'sikkim',
    lat: 27.3389,
    lng: 88.6065,
    riskLevel: 'HIGH',
    rainfall24hMm: 172.0,
    soilMoisturePct: 86,
    slopeAngleDeg: 49,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '4 mins ago',
  },
  {
    id: 'ST-06',
    name: 'Tawang Glacier Pass Monitor',
    stateId: 'arunachal',
    lat: 27.5860,
    lng: 91.8594,
    riskLevel: 'CRITICAL',
    rainfall24hMm: 245.0,
    soilMoisturePct: 91,
    slopeAngleDeg: 52,
    sensorHealth: 'DEGRADED',
    lastUpdated: '12 mins ago',
  },
  {
    id: 'ST-07',
    name: 'Kohima North Slope Station',
    stateId: 'nagaland',
    lat: 25.6751,
    lng: 94.1086,
    riskLevel: 'HIGH',
    rainfall24hMm: 138.8,
    soilMoisturePct: 78,
    slopeAngleDeg: 36,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '10 mins ago',
  },
  {
    id: 'ST-08',
    name: 'Imphal Valley Basin Sentry',
    stateId: 'manipur',
    lat: 24.8170,
    lng: 93.9368,
    riskLevel: 'MEDIUM',
    rainfall24hMm: 96.5,
    soilMoisturePct: 69,
    slopeAngleDeg: 24,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '15 mins ago',
  },
  {
    id: 'ST-09',
    name: 'Aizawl Central Ridge Node',
    stateId: 'mizoram',
    lat: 23.7271,
    lng: 92.7176,
    riskLevel: 'MEDIUM',
    rainfall24hMm: 114.2,
    soilMoisturePct: 74,
    slopeAngleDeg: 31,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '6 mins ago',
  },
  {
    id: 'ST-10',
    name: 'Agartala West Boundary Station',
    stateId: 'tripura',
    lat: 23.8315,
    lng: 91.2868,
    riskLevel: 'LOW',
    rainfall24hMm: 58.0,
    soilMoisturePct: 56,
    slopeAngleDeg: 14,
    sensorHealth: 'OPERATIONAL',
    lastUpdated: '18 mins ago',
  },
];

// Helper to construct GeoJSON FeatureCollection for MapLibre GL
export function getNeStatesGeoJson() {
  return {
    type: 'FeatureCollection',
    features: NORTHEAST_STATES.map((state) => ({
      type: 'Feature',
      id: state.id,
      properties: {
        id: state.id,
        name: state.name,
        code: state.code,
        riskLevel: state.riskLevel,
        avgRainfall: state.avgRainfall24h,
        soilMoisture: state.avgSoilMoisture,
        elevationRange: state.elevationRange,
      },
      geometry: {
        type: 'Polygon',
        coordinates: state.polygonCoords,
      },
    })),
  };
}
