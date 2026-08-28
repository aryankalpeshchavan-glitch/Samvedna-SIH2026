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
  }, []);

  return { location, refreshLocation };
}
