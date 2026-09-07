/**
 * Typed contracts matching CrisisCore FastAPI Backend OpenAPI specifications.
 */

export type BackendIncidentType = 'landslide' | 'flood' | 'earthquake' | 'fire' | 'other';

export interface IncidentCreatePayload {
  type: BackendIncidentType;
  description: string;
  lat: number;
  lng: number;
  severity?: number;
  photo_url?: string | null;
  idempotency_key?: string | null;
}

export interface IncidentOut {
  id: string;
  reporter_id: number;
  type: BackendIncidentType;
  description: string;
  lat: number;
  lng: number;
  severity: number;
  status: string;
  data_label: string;
  photo_url?: string | null;
  occurred_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssignmentStatusInfo {
  id: string;
  volunteer_id: number;
  status: string;
  sla_deadline: string;
}

export interface IncidentStatusResponse {
  incident_id: string;
  status: string;
  severity: number;
  assignment?: AssignmentStatusInfo | null;
  updated_at: string;
}

export interface RiskZoneOut {
  id: string;
  risk_score: number;
  horizon_hours: number;
  top_features?: Record<string, any>;
  data_label?: string;
  data_status?: string | null;
  computed_at: string;
  lat?: number | null;
  lng?: number | null;
  confidence?: number | null;
  model_version?: string | null;
  state?: string | null;
  district?: string | null;
  risk_level?: string | null;
}

export function classifyRiskLevel(score: number): 'LOW' | 'MEDIUM' | 'HIGH' {
  if (score >= 0.7) return 'HIGH';
  if (score >= 0.4) return 'MEDIUM';
  return 'LOW';
}

export interface RiskPredictionResponse {
  risk_score: number;
  risk_level: string;
  confidence: number;
  drivers: string[];
  data_status: string;
  model_version?: string | null;
  feature_attributions?: Record<string, number> | null;
  state?: string | null;
  district?: string | null;
  threshold?: number | null;
  prediction_time?: string | null;
}

/**
 * Explicit mapping from frontend incident categories to backend IncidentType enum.
 * Non-standard categories are mapped to the closest standard category.
 */
export function mapCategoryToBackendType(category?: string | null): BackendIncidentType {
  if (!category) return 'other';
  const c = category.toUpperCase().trim();
  switch (c) {
    case 'LANDSLIDE':
    case 'SLOPE_CRACK':
      return 'landslide';
    case 'FLOOD':
    case 'FLASH_FLOOD':
      return 'flood';
    case 'FIRE':
      return 'fire';
    case 'EARTHQUAKE':
      return 'earthquake';
    case 'ROAD_BLOCKED':
    case 'BUILDING_DAMAGE':
    case 'PERSON_TRAPPED':
    case 'MEDICAL_EMERGENCY':
    case 'OTHER':
    default:
      return 'other';
  }
}

/**
 * Explicit mapping from frontend severity string levels to backend integer 1..5.
 */
export function mapSeverityToInteger(severity?: string | number | null): number {
  if (typeof severity === 'number') {
    return Math.max(1, Math.min(5, Math.round(severity)));
  }
  if (!severity) return 3;
  const s = severity.toUpperCase().trim();
  switch (s) {
    case 'LOW':
      return 1;
    case 'WATCH':
      return 2;
    case 'MEDIUM':
      return 3;
    case 'HIGH':
      return 4;
    case 'CRITICAL':
      return 5;
    default:
      return 3;
  }
}
