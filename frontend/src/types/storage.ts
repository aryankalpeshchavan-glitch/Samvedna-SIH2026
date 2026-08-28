import { SosPayload, IncidentReportPayload } from './emergency';

export type PendingActionType = 'SOS' | 'INCIDENT_REPORT';

export type PendingItemStatus = 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED';

export interface PendingActionEntry {
  id: string;
  type: PendingActionType;
  payload: SosPayload | IncidentReportPayload;
  createdAt: number;
  status: PendingItemStatus;
  attempts: number;
  lastError?: string;
  syncedAt?: number;
}

export interface PendingSosEntry {
  id: string;
  payload: SosPayload;
  createdAt: number;
  synced: boolean;
  attempts: number;
}
