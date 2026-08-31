import { LocationData, LocationStatus } from '../types/emergency';
import { Geolocation } from '@capacitor/geolocation';
import { Capacitor } from '@capacitor/core';

let cachedLocation: LocationData = {
  latitude: null,
  longitude: null,
  status: 'REQUESTING_LOCATION',
};

export async function getCurrentLocation(): Promise<LocationData> {
  // If we already have a detected location, return cached immediately
  if (cachedLocation.status === 'LOCATION_DETECTED' && cachedLocation.latitude && cachedLocation.longitude) {
    // Refresh in background
    triggerBackgroundGps();
    return cachedLocation;
  }

  // Try instant IP fallback first for zero-wait coordinates
  const ipLocation = await tryIpFallback('REQUESTING_LOCATION');
  
  // Trigger hardware GPS fix
  triggerBackgroundGps();

  return ipLocation;
}

async function triggerBackgroundGps() {
  try {
    if (Capacitor.isNativePlatform()) {
      const permission = await Geolocation.checkPermissions();
      if (permission.location !== 'granted') {
        const req = await Geolocation.requestPermissions();
        if (req.location !== 'granted') {
          console.warn('Native GPS permission denied');
          return;
        }
      }
    }

    const pos = await Geolocation.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 6000,
      maximumAge: 10000,
    });

    cachedLocation = {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      accuracy: pos.coords.accuracy,
      status: 'LOCATION_DETECTED',
      timestamp: pos.timestamp,
    };
  } catch (err: any) {
    console.warn('GPS notice:', err.message || err);
  }
}

async function tryIpFallback(status: LocationStatus): Promise<LocationData> {
  const apis = [
    'https://freeipapi.com/api/json',
    'https://ipwho.is/',
    'https://ipapi.co/json/',
  ];

  for (const url of apis) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const lat = data.latitude ?? data.lat;
        const lng = data.longitude ?? data.lng ?? data.lon;
        if (lat !== undefined && lng !== undefined && !isNaN(Number(lat)) && !isNaN(Number(lng))) {
          cachedLocation = {
            latitude: Number(lat),
            longitude: Number(lng),
            accuracy: 3000,
            status: 'LOCATION_DETECTED',
            timestamp: Date.now(),
          };
          return cachedLocation;
        }
      }
    } catch (e) {
      console.warn(`IP location provider ${url} failed:`, e);
    }
  }

  cachedLocation = {
    latitude: null,
    longitude: null,
    status,
  };
  return cachedLocation;
}

export function getCachedLocation(): LocationData {
  return cachedLocation;
}
