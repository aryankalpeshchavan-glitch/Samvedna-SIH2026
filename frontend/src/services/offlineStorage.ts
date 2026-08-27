import { openDB, IDBPDatabase } from 'idb';
import { SosPayload } from '../types/emergency';
import { PendingSosEntry } from '../types/storage';

const DB_NAME = 'crisiscore_db';
const STORE_NAME = 'pending_sos';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase> | null = null;

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          store.createIndex('createdAt', 'createdAt');
          store.createIndex('synced', 'synced');
        }
      },
    });
  }
  return dbPromise;
}

export async function savePendingSOS(payload: SosPayload): Promise<PendingSosEntry> {
  const db = await getDB();
  const entry: PendingSosEntry = {
    id: payload.sosId,
    payload,
    createdAt: Date.now(),
    synced: false,
    attempts: 0,
  };
  await db.put(STORE_NAME, entry);
  console.log('[OfflineStorage] Saved pending SOS locally:', entry.id);
  return entry;
}

export async function getPendingSOS(): Promise<PendingSosEntry[]> {
  try {
    const db = await getDB();
    const all = await db.getAll(STORE_NAME);
    return all.sort((a, b) => b.createdAt - a.createdAt);
  } catch (err) {
    console.error('[OfflineStorage] Error reading pending SOS:', err);
    return [];
  }
}

export async function removePendingSOS(id: string): Promise<void> {
  try {
    const db = await getDB();
    await db.delete(STORE_NAME, id);
    console.log('[OfflineStorage] Removed pending SOS:', id);
  } catch (err) {
    console.error('[OfflineStorage] Error deleting pending SOS:', err);
  }
}

export async function markSOSAsSynced(id: string): Promise<void> {
  try {
    const db = await getDB();
    const entry = await db.get(STORE_NAME, id);
    if (entry) {
      entry.synced = true;
      await db.put(STORE_NAME, entry);
      console.log('[OfflineStorage] Marked SOS as synced:', id);
    }
  } catch (err) {
    console.error('[OfflineStorage] Error marking SOS as synced:', err);
  }
}
