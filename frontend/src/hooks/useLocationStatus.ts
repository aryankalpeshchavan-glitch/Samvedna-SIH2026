import { useState, useEffect } from 'react';
import { LocationData } from '../types/emergency';
import { getCurrentLocation, getCachedLocation } from '../services/location';

export function useLocationStatus(): { location: LocationData; refreshLocation: () => Promise<LocationData> } {
  const [location, setLocation] = useState<LocationData>(getCachedLocation());

  const refreshLocation = async () => {
    setLocation((prev) => ({ ...prev, status: 'REQUESTING_LOCATION' }));
    const loc = await getCurrentLocation();
    setLocation(loc);
    return loc;
  };

  useEffect(() => {
    refreshLocation();

    if ('geolocation' in navigator) {
      const watchId = navigator.geolocation.watchPosition(
        (pos) => {
          setLocation({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            status: 'LOCATION_DETECTED',
            timestamp: pos.timestamp,
          });
        },
        (err) => {
          console.warn('Geolocation watch error:', err);
        },
        {
          enableHighAccuracy: true,
          timeout: 15000,
          maximumAge: 0,
        }
      );

      return () => navigator.geolocation.clearWatch(watchId);
    }
  }, []);

  return { location, refreshLocation };
}
