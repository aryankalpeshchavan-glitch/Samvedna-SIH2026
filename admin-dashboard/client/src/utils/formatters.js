export function timeAgo(timestamp) {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export function formatEta(seconds) {
  if (!seconds || seconds <= 0) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m > 60) {
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return `${h}h ${rm}m`;
  }
  return `${m}m ${String(s).padStart(2, '0')}s`;
}

export function formatDistance(km) {
  if (km < 1) return `${(km * 1000).toFixed(0)}m`;
  return `${km.toFixed(1)} km`;
}

export function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

export function getStatusClass(status) {
  const map = {
    'SAFE': 'status-safe',
    'IN ZONE': 'status-inzone',
    'NOTIFIED': 'status-notified',
    'EVACUATED': 'status-evacuated',
    'STANDBY': 'status-standby',
    'EN ROUTE': 'status-enroute',
    'ON SITE': 'status-onsite'
  };
  return map[status] || 'status-safe';
}

export function getSeverityClass(severity) {
  const map = {
    'HIGH': 'badge-high',
    'MEDIUM': 'badge-medium',
    'LOW': 'badge-low'
  };
  return map[severity] || 'badge-low';
}

export function getUnitIcon(type) {
  const map = {
    'Rescue Team': '🚒',
    'Medical Unit': '🚑',
    'Helicopter': '🚁',
    'Engineering': '🔧'
  };
  return map[type] || '🚗';
}

export function clockTime() {
  return new Date().toLocaleTimeString('en-US', { hour12: false });
}
