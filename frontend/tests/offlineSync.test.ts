import test, { beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import 'fake-indexeddb/auto';
import { mockApiSyncItem, processPendingQueue } from '../src/services/offlineSync';
import { savePendingAction, getPendingActions, removePendingAction } from '../src/services/offlineStorage';
import { PendingActionEntry } from '../src/types/storage';
import { SosPayload } from '../src/types/emergency';

// In-memory mock for localStorage
class MockLocalStorage {
  private store = new Map<string, string>();
  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }
  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }
  removeItem(key: string): void {
    this.store.delete(key);
  }
  clear(): void {
    this.store.clear();
  }
}

const mockLocalStorage = new MockLocalStorage();
(globalThis as any).localStorage = mockLocalStorage;

function createTestEntry(id: string): PendingActionEntry {
  const payload: SosPayload = {
    sosId: id,
    timestamp: Date.now(),
    location: {
      latitude: 26.14,
      longitude: 91.73,
      status: 'LOCATION_DETECTED',
      addressName: 'Guwahati Test Sector',
    },
    incidentType: 'LANDSLIDE',
    note: 'Test offline emergency',
    networkStatusOnTrigger: 'OFFLINE',
    dataSource: 'synthetic',
  };
  return {
    id,
    type: 'SOS',
    payload,
    createdAt: Date.now(),
    status: 'PENDING',
    attempts: 0,
  };
}

// Reset localStorage and clear pending actions between tests
async function resetTestState() {
  mockLocalStorage.clear();
  const all = await getPendingActions();
  for (const item of all) {
    await removePendingAction(item.id);
  }
}

beforeEach(async () => {
  await resetTestState();
});

afterEach(async () => {
  await resetTestState();
});

// ─── A. Missing Auth Token ───────────────────────────────────────────────────

test('A. Missing auth token: mockApiSyncItem returns false and does not call fetch', async () => {
  let fetchCalled = false;
  globalThis.fetch = async () => {
    fetchCalled = true;
    return new Response(JSON.stringify({ id: 'inc-1' }), { status: 201 });
  };

  const item = createTestEntry('SOS-NO-TOKEN-1');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, false, 'Sync must return false when token is missing');
  assert.strictEqual(fetchCalled, false, 'fetch must NOT be called when token is missing');
});

test('A. Missing auth token: processPendingQueue leaves item queued as FAILED and never removed', async () => {
  const item = createTestEntry('SOS-NO-TOKEN-QUEUE');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 0, 'No items should be marked synced');
  assert.strictEqual(res.failedCount, 1, 'Item should be marked failed');

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 1, 'Item MUST remain in IndexedDB queue');
  assert.strictEqual(pending[0].status, 'FAILED', 'Item status must be FAILED');
  assert.strictEqual(pending[0].attempts, 1, 'Attempts counter must be incremented');
  assert.notStrictEqual(pending[0].status, 'SYNCED', 'Item must NOT be marked SYNCED');
});

// ─── B. HTTP 401 Unauthorized ────────────────────────────────────────────────

test('B. HTTP 401 Unauthorized: mockApiSyncItem returns false and does not succeed', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'expired-or-invalid-token');
  globalThis.fetch = async () => new Response('Unauthorized token', { status: 401 });

  const item = createTestEntry('SOS-HTTP-401');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, false, 'Sync must return false on HTTP 401');
});

test('B. HTTP 401: processPendingQueue marks FAILED and preserves item in queue', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'bad-token');
  globalThis.fetch = async () => new Response('Unauthorized', { status: 401 });

  const item = createTestEntry('SOS-QUEUE-401');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 0);
  assert.strictEqual(res.failedCount, 1);

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 1, 'Item must remain in queue on 401');
  assert.strictEqual(pending[0].status, 'FAILED');
  assert.strictEqual(pending[0].attempts, 1);
});

// ─── C. HTTP 422 Unprocessable Entity ────────────────────────────────────────

test('C. HTTP 422: mockApiSyncItem returns false on validation error', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ detail: 'Invalid coordinate bounds' }), { status: 422 });

  const item = createTestEntry('SOS-HTTP-422');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, false, 'Sync must return false on HTTP 422');
});

test('C. HTTP 422: processPendingQueue keeps item queued with FAILED state', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () => new Response('Validation Error', { status: 422 });

  const item = createTestEntry('SOS-QUEUE-422');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 0);
  assert.strictEqual(res.failedCount, 1);

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 1, 'Item must remain in queue on 422');
  assert.strictEqual(pending[0].status, 'FAILED');
});

// ─── D. HTTP 500 Internal Server Error ───────────────────────────────────────

test('D. HTTP 500: mockApiSyncItem returns false and never treats 500 as success', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () => new Response('Internal Server Error', { status: 500 });

  const item = createTestEntry('SOS-HTTP-500');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, false, 'Sync must return false on HTTP 500');
});

test('D. HTTP 500: processPendingQueue keeps item queued for retry', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () => new Response('DB connection failed', { status: 500 });

  const item = createTestEntry('SOS-QUEUE-500');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 0);
  assert.strictEqual(res.failedCount, 1);

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 1, 'Item must remain queued on 500 error');
  assert.strictEqual(pending[0].status, 'FAILED');
});

// ─── E. Successful HTTP 200/201 ──────────────────────────────────────────────

test('E. HTTP 201 Created: mockApiSyncItem returns true', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ id: 'inc-999', status: 'reported' }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });

  const item = createTestEntry('SOS-HTTP-201');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, true, 'Sync must return true on HTTP 201 Created');
});

test('E. HTTP 200 OK: processPendingQueue marks SYNCED and removes item', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ id: 'inc-999', status: 'reported' }), { status: 200 });

  const item = createTestEntry('SOS-QUEUE-200');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 1, 'Item must be counted as synced');
  assert.strictEqual(res.failedCount, 0, 'Zero failed items');

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 0, 'Successfully acknowledged item must be removed from queue');
});

// ─── F. Network Exception / Fetch Throws ─────────────────────────────────────

test('F. Network Exception: mockApiSyncItem catches error and returns false', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () => {
    throw new TypeError('Failed to fetch: Network unreachable');
  };

  const item = createTestEntry('SOS-NETWORK-FAIL');
  const result = await mockApiSyncItem(item);

  assert.strictEqual(result, false, 'Sync must return false when fetch throws network error');
});

test('F. Network Exception: processPendingQueue keeps item in queue with incremented attempts', async () => {
  mockLocalStorage.setItem('crisiscore_token', 'valid-token');
  globalThis.fetch = async () => {
    throw new TypeError('Connection refused');
  };

  const item = createTestEntry('SOS-QUEUE-NET-FAIL');
  await savePendingAction('SOS', item.payload as SosPayload);

  const res = await processPendingQueue(mockApiSyncItem);

  assert.strictEqual(res.syncedCount, 0);
  assert.strictEqual(res.failedCount, 1);

  const pending = await getPendingActions();
  assert.strictEqual(pending.length, 1, 'Item must be retained in queue after network error');
  assert.strictEqual(pending[0].status, 'FAILED');
  assert.strictEqual(pending[0].attempts, 1);
});

// ─── G. Regression Invariant (No False Removal on Any Failure) ────────────────

test('G. Regression Invariant: multiple failing statuses (400, 403, 429, 502, 503) never remove items', async () => {
  const failureStatuses = [400, 403, 429, 502, 503];
  mockLocalStorage.setItem('crisiscore_token', 'token-xyz');

  for (const status of failureStatuses) {
    globalThis.fetch = async () => new Response(`Error ${status}`, { status });

    const item = createTestEntry(`SOS-FAIL-${status}`);
    await savePendingAction('SOS', item.payload as SosPayload);

    const res = await processPendingQueue(mockApiSyncItem);

    assert.strictEqual(res.syncedCount, 0, `Status ${status} must not be counted as synced`);
    assert.strictEqual(res.failedCount, 1, `Status ${status} must be counted as failed`);

    const pending = await getPendingActions();
    const found = pending.find((p) => p.id === item.id);
    assert.ok(found, `Item ${item.id} must NOT be removed from queue on HTTP ${status}`);
    assert.strictEqual(found?.status, 'FAILED', `Item ${item.id} must be marked FAILED`);

    // Clean up
    await resetTestState();
  }
});
