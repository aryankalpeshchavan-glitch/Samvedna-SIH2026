import { getPendingActions, markActionStatus, removePendingAction } from './offlineStorage';
import { PendingActionEntry } from '../types/storage';

export type SyncState = 'IDLE' | 'SYNCING' | 'SYNCED' | 'ERROR';

/**
 * Mock API Transmission Layer
 * 
 * NOTE FOR BACKEND TEAM:
 * Replace `mockApiSyncItem` with your real backend endpoint call:
 * `const res = await fetch('/api/v1/emergency/sync', { method: 'POST', body: JSON.stringify(item) });`
 */
export async function mockApiSyncItem(item: PendingActionEntry): Promise<boolean> {
  console.log(`[OfflineSync] Transmitting pending [${item.type}] ${item.id} to CrisisCore Server...`);
  // Simulate network roundtrip latency (900ms per payload)
  await new Promise((resolve) => setTimeout(resolve, 900));
  return true;
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
        await markActionStatus(item.id, 'FAILED', 'Server responded with rejection');
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
