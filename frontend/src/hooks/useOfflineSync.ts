import { useState, useEffect, useCallback } from 'react';
import { useNetworkStatus } from './useNetworkStatus';
import { getPendingActions } from '../services/offlineStorage';
import { processPendingQueue, SyncState } from '../services/offlineSync';
import { PendingActionEntry } from '../types/storage';

export function useOfflineSync() {
  const networkStatus = useNetworkStatus();
  const [syncState, setSyncState] = useState<SyncState>('IDLE');
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [pendingItems, setPendingItems] = useState<PendingActionEntry[]>([]);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(null);

  // Refresh pending count and items list from IndexedDB
  const refreshPending = useCallback(async () => {
    const items = await getPendingActions();
    const activePending = items.filter((item) => item.status !== 'SYNCED');
    setPendingItems(items);
    setPendingCount(activePending.length);
  }, []);

  // Process and transmit pending queue
  const triggerSync = useCallback(async () => {
    const items = await getPendingActions();
    const active = items.filter((item) => item.status !== 'SYNCED');

    if (active.length === 0) {
      setSyncState('IDLE');
      return;
    }

    setSyncState('SYNCING');
    const result = await processPendingQueue();
    await refreshPending();

    if (result.syncedCount > 0 && result.failedCount === 0) {
      setSyncState('SYNCED');
      setLastSyncedAt(Date.now());
      // Reset back to IDLE after 4s
      setTimeout(() => setSyncState('IDLE'), 4000);
    } else if (result.failedCount > 0) {
      setSyncState('ERROR');
    } else {
      setSyncState('IDLE');
    }
  }, [refreshPending]);

  // Automatic sync trigger when connection restores to ONLINE
  useEffect(() => {
    refreshPending();
    if (networkStatus === 'ONLINE') {
      triggerSync();
    }
  }, [networkStatus, triggerSync, refreshPending]);

  return {
    syncState,
    pendingCount,
    pendingItems,
    lastSyncedAt,
    refreshPending,
    triggerSync,
  };
}
