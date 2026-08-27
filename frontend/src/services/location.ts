import { LocationData, LocationStatus } from '../types/emergency';

let cachedLocation: LocationData = {
  latitude: null,
  longitude: null,
  status: 'REQUESTING_LOCATION',
};

export async function getCurrentLocation(): Promise<LocationData> {
  if (!('geolocation' in navigator)) {
    cachedLocation = {
      latitude: null,
      longitude: null,
      status: 'LOCATION_UNAVAILABLE',
    };
    return cachedLocation;
  }

  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        cachedLocation = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
          status: 'LOCATION_DETECTED',
          timestamp: pos.timestamp,
        };
        resolve(cachedLocation);
      },
      (err) => {
        let status: LocationStatus = 'LOCATION_UNAVAILABLE';
        if (err.code === err.PERMISSION_DENIED) {
          status = 'PERMISSION_DENIED';
        }
        cachedLocation = {
          latitude: null,
          longitude: null,
          status,
        };
        resolve(cachedLocation);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      }
    );
  });
}

export function getCachedLocation(): LocationData {
  return cachedLocation;
}
