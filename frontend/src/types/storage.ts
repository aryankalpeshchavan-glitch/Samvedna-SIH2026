import { SosPayload } from './emergency';

export interface PendingSosEntry {
  id: string;
  payload: SosPayload;
  createdAt: number;
  synced: boolean;
  attempts: number;
}
