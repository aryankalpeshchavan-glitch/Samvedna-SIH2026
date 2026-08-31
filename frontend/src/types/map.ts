import { SeverityLevel } from './emergency';

export type NeStateId = 
  | 'assam'
  | 'arunachal'
  | 'meghalaya'
  | 'manipur'
  | 'mizoram'
  | 'nagaland'
  | 'tripura'
  | 'sikkim';

export type MapLayerMode = 
  | 'terrain' 
  | 'risk' 
  | 'rainfall' 
  | 'moisture' 
  | 'citizen_reports' 
  | 'safe_route';

export interface NeStateInfo {
  id: NeStateId;
  name: string;
  code: string;
  capital: string;
  riskLevel: SeverityLevel;
  center: [number, number]; // [lat, lng]
  avgRainfall24h: number; // in mm
  elevationRange: string;
  activeLandslideZones: number;
  avgSoilMoisture: number; // in %
  polygonCoords: [number, number][][];
  heightOffset: number;
}

export interface MonitoringPoint {
  id: string;
  name: string;
  stateId: NeStateId;
  lat: number;
  lng: number;
  riskLevel: SeverityLevel;
  rainfall24hMm: number;
  soilMoisturePct: number;
  slopeAngleDeg: number;
  sensorHealth: 'OPERATIONAL' | 'DEGRADED' | 'OFFLINE';
  lastUpdated: string;
}

export interface WhyRiskStep {
  stepNumber: string;
  title: string;
  value: string;
  unit?: string;
  description: string;
  statusColor: string;
}

export interface TerrainScanResult {
  elevationMeters: number;
  slopeDegrees: number;
  rainfall24hMm: number;
  soilMoisturePct: number;
  historicalIncidentCount: number;
  riskScore: number; // 0-100
  riskCategory: SeverityLevel;
  recommendation: string;
}

export interface SafeRouteInfo {
  id: string;
  title: string;
  distanceKm: number;
  estMinutes: number;
  shelterName: string;
  shelterCapacity: number;
  shelterOccupancyPct: number;
  blockedRoads: string[];
  safePathCoords: [number, number][]; // [lng, lat]
}
