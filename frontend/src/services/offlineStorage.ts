import { openDB, IDBPDatabase } from 'idb';
import { SosPayload, IncidentReportPayload } from '../types/emergency';
import { PendingActionEntry, PendingActionType, PendingItemStatus, PendingSosEntry } from '../types/storage';

const DB_NAME = 'samvedna_offline_db';
const STORE_ACTIONS = 'pending_actions';
const STORE_SOS = 'pending_sos';
const DB_VERSION = 2;

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDB(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        if (oldVersion < 1 && !db.objectStoreNames.contains(STORE_SOS)) {
          const sosStore = db.createObjectStore(STORE_SOS, { keyPath: 'id' });
          sosStore.createIndex('createdAt', 'createdAt');
          sosStore.createIndex('synced', 'synced');
        }
        if (!db.objectStoreNames.contains(STORE_ACTIONS)) {
          const actionStore = db.createObjectStore(STORE_ACTIONS, { keyPath: 'id' });
          actionStore.createIndex('type', 'type');
          actionStore.createIndex('createdAt', 'createdAt');
          actionStore.createIndex('status', 'status');
        }
      },
    });
  }
  return dbPromise;
}

// ----------------------------------------------------
// Unified Generic Offline Pending Queue Storage
// ----------------------------------------------------

export async function savePendingAction(
  type: PendingActionType,
  payload: SosPayload | IncidentReportPayload
): Promise<PendingActionEntry> {
  const db = await getDB();
  const entry: PendingActionEntry = {
    id: 'id' in payload ? payload.id : payload.sosId,
    type,
    payload,
    createdAt: Date.now(),
    status: 'PENDING',
    attempts: 0,
  };

  await db.put(STORE_ACTIONS, entry);
  console.log(`[OfflineStorage] Saved pending action [${type}] to IndexedDB:`, entry.id);

  // Also maintain backward-compatibility with pending_sos store if SOS
  if (type === 'SOS') {
    await savePendingSOS(payload as SosPayload);
  }

  return entry;
}

export async function getPendingActions(): Promise<PendingActionEntry[]> {
  try {
    const db = await getDB();
    const all = await db.getAll(STORE_ACTIONS);
    return all.sort((a, b) => b.createdAt - a.createdAt);
  } catch (err) {
    console.error('[OfflineStorage] Error reading pending actions:', err);
    return [];
  }
}

export async function getPendingCount(): Promise<number> {
  try {
    const actions = await getPendingActions();
    return actions.filter((item) => item.status !== 'SYNCED').length;
  } catch {
    return 0;
  }
}

export async function markActionStatus(
  id: string,
  status: PendingItemStatus,
  error?: string
): Promise<void> {
  try {
    const db = await getDB();
    const entry = await db.get(STORE_ACTIONS, id);
    if (entry) {
      entry.status = status;
      entry.attempts = (entry.attempts || 0) + (status === 'FAILED' ? 1 : 0);
      if (error) entry.lastError = error;
      if (status === 'SYNCED') entry.syncedAt = Date.now();
      await db.put(STORE_ACTIONS, entry);
      console.log(`[OfflineStorage] Updated action status [${id}]:`, status);
    }
  } catch (err) {
    console.error('[OfflineStorage] Error updating action status:', err);
  }
}

export async function removePendingAction(id: string): Promise<void> {
  try {
    const db = await getDB();
    await db.delete(STORE_ACTIONS, id);
    await removePendingSOS(id);
    console.log('[OfflineStorage] Removed pending action from IndexedDB:', id);
  } catch (err) {
    console.error('[OfflineStorage] Error deleting pending action:', err);
  }
}

export async function clearSyncedActions(): Promise<void> {
  try {
    const actions = await getPendingActions();
    const db = await getDB();
    for (const act of actions) {
      if (act.status === 'SYNCED') {
        await db.delete(STORE_ACTIONS, act.id);
      }
    }
  } catch (err) {
    console.error('[OfflineStorage] Error clearing synced actions:', err);
  }
}

// ----------------------------------------------------
// Backward-Compatibility Helpers for Existing SOS State
// ----------------------------------------------------

export async function savePendingSOS(payload: SosPayload): Promise<PendingSosEntry> {
  const db = await getDB();
  const entry: PendingSosEntry = {
    id: payload.sosId,
    payload,
    createdAt: Date.now(),
    synced: false,
    attempts: 0,
  };
  await db.put(STORE_SOS, entry);
  return entry;
}

export async function getPendingSOS(): Promise<PendingSosEntry[]> {
  try {
    const db = await getDB();
    const all = await db.getAll(STORE_SOS);
    return all.sort((a, b) => b.createdAt - a.createdAt);
  } catch {
    return [];
  }
}

export async function removePendingSOS(id: string): Promise<void> {
  try {
    const db = await getDB();
    await db.delete(STORE_SOS, id);
  } catch {
    // Ignore error
  }
}

export async function markSOSAsSynced(id: string): Promise<void> {
  try {
    const db = await getDB();
    const entry = await db.get(STORE_SOS, id);
    if (entry) {
      entry.synced = true;
      await db.put(STORE_SOS, entry);
    }
  } catch {
    // Ignore error
  }
}
