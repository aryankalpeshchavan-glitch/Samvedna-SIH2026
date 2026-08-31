export type SosState = 
  | 'IDLE'
  | 'SOS_CONFIRMATION'
  | 'SENDING'
  | 'SENT'
  | 'OFFLINE_QUEUED'
  | 'ERROR'
  | 'VERIFIED'
  | 'ASSIGNED'
  | 'VOLUNTEER_EN_ROUTE'
  | 'HELP_ARRIVED'
  | 'RESOLVED';

export type IncidentCategory = 
  | 'LANDSLIDE'
  | 'SLOPE_CRACK'
  | 'ROAD_BLOCKED'
  | 'FLOOD'
  | 'FLASH_FLOOD'
  | 'BUILDING_DAMAGE'
  | 'PERSON_TRAPPED'
  | 'MEDICAL_EMERGENCY'
  | 'FIRE'
  | 'OTHER';

export type SeverityLevel = 'LOW' | 'WATCH' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type DataSourceType = 'live' | 'synthetic' | 'replayed';

export type LocationStatus = 
  | 'LOCATION_DETECTED'
  | 'LOCATION_UNAVAILABLE'
  | 'REQUESTING_LOCATION'
  | 'PERMISSION_DENIED';

export type NetworkStatusType = 'ONLINE' | 'WEAK' | 'OFFLINE';

export interface LocationData {
  latitude: number | null;
  longitude: number | null;
  accuracy?: number | null;
  addressName?: string;
  status: LocationStatus;
  timestamp?: number;
}

export interface IncidentReportPayload {
  id: string;
  category: IncidentCategory;
  description?: string;
  severity: SeverityLevel;
  location: LocationData;
  timestamp: number;
  contactNumber?: string;
  photoUrl?: string;
}

export interface CitizenMapReport {
  id: string;
  category: IncidentCategory;
  title: string;
  locationName: string;
  lat: number;
  lng: number;
  severity: SeverityLevel;
  reportedTimeAgo: string;
  verifiedStatus: 'VERIFIED' | 'UNVERIFIED' | 'INVESTIGATING';
  description: string;
  imageUrl?: string;
}

export interface SosPayload {
  sosId: string;
  timestamp: number;
  location: LocationData;
  incidentType?: IncidentCategory;
  note?: string;
  networkStatusOnTrigger: NetworkStatusType;
  dataSource: DataSourceType;
}

export interface SosStatusDetail {
  state: SosState;
  sosId?: string;
  timestamp?: number;
  assignedVolunteerName?: string;
  assignedVolunteerPhone?: string;
  etaMinutes?: number;
  lastUpdatedText?: string;
  errorMessage?: string;
}
