import { NetworkStatusType } from '../types/emergency';

type NetworkCallback = (status: NetworkStatusType) => void;

let currentStatus: NetworkStatusType = navigator.onLine ? 'ONLINE' : 'OFFLINE';
const listeners: Set<NetworkCallback> = new Set();

function updateStatus() {
  const isOnline = navigator.onLine;
  // Basic weak connection estimation via Network Information API if available
  let status: NetworkStatusType = isOnline ? 'ONLINE' : 'OFFLINE';
  
  if (isOnline && 'connection' in navigator) {
    const conn = (navigator as unknown as { connection?: { effectiveType?: string; rtt?: number } }).connection;
    if (conn) {
      if (conn.effectiveType === '2g' || conn.effectiveType === 'slow-2g' || (conn.rtt && conn.rtt > 1000)) {
        status = 'WEAK';
      }
    }
  }

  if (status !== currentStatus) {
    currentStatus = status;
    listeners.forEach((cb) => cb(currentStatus));
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  if ('connection' in navigator) {
    const conn = (navigator as unknown as { connection?: EventTarget }).connection;
    conn?.addEventListener?.('change', updateStatus);
  }
}

export function getNetworkStatus(): NetworkStatusType {
  updateStatus();
  return currentStatus;
}

export function subscribeNetworkStatus(callback: NetworkCallback): () => void {
  listeners.add(callback);
  callback(currentStatus);
  return () => {
    listeners.delete(callback);
  };
}
