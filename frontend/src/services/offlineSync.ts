import { getPendingActions, markActionStatus, removePendingAction } from './offlineStorage';
import { PendingActionEntry } from '../types/storage';

export type SyncState = 'IDLE' | 'SYNCING' | 'SYNCED' | 'ERROR';

/**
 * Real API Transmission Layer — syncs queued SOS to backend /incidents.
 * Returns true ONLY on HTTP 2xx server acknowledgement.
 * Returns false on missing auth token, non-2xx response, or network failure.
 */
export async function mockApiSyncItem(item: PendingActionEntry): Promise<boolean> {
  console.log(`[OfflineSync] Transmitting pending [${item.type}] ${item.id} to CrisisCore Server...`);

  // 1. Check for authentication token before attempting network request
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('crisiscore_token') : null;
  if (!token || !token.trim()) {
    console.warn(`[OfflineSync] Missing authentication token. Cannot sync pending item: ${item.id}`);
    return false;
  }

  try {
    const payload = item.payload as unknown as {
      sosId?: string;
      location?: { latitude: number; longitude: number };
      incidentType?: string;
      note?: string;
    };
    const lat = payload.location?.latitude ?? 26.14;
    const lng = payload.location?.longitude ?? 91.73;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };

    const res = await fetch('/incidents', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        type: (payload.incidentType || 'other').toLowerCase(),
        description: payload.note || `Queued SOS ${item.id}`,
        lat,
        lng,
        severity: 3,
        idempotency_key: item.id,
      }),
    });

    if (res.ok) {
      return true;
    }

    let errorBody = '';
    try {
      errorBody = await res.text();
    } catch {
      // ignore body read error
    }
    console.warn(`[OfflineSync] Backend rejected item ${item.id} (HTTP ${res.status}):`, errorBody);
    return false;
  } catch (e) {
    console.warn(`[OfflineSync] Network error syncing item ${item.id}, will retry:`, e);
    return false;
  }
}

/**
 * Process the local IndexedDB pending queue
 */
export async function processPendingQueue(
  apiSyncFn: (item: PendingActionEntry) => Promise<boolean> = mockApiSyncItem
): Promise<{ syncedCount: number; failedCount: number }> {
  const pending = await getPendingActions();
  const unSynced = pending.filter((item) => item.status !== 'SYNCED');

  if (unSynced.length === 0) {
    return { syncedCount: 0, failedCount: 0 };
  }

  let syncedCount = 0;
  let failedCount = 0;

  for (const item of unSynced) {
    try {
      await markActionStatus(item.id, 'SYNCING');
      const success = await apiSyncFn(item);

      if (success) {
        await markActionStatus(item.id, 'SYNCED');
        // Remove item after clean transmission
        await removePendingAction(item.id);
        syncedCount++;
      } else {
        await markActionStatus(item.id, 'FAILED', 'Server rejected or missing authentication token');
        failedCount++;
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Network transmission error';
      await markActionStatus(item.id, 'FAILED', errMsg);
      failedCount++;
    }
  }

  return { syncedCount, failedCount };
}
