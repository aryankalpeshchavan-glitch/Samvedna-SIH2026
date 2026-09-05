import { useState, useEffect } from 'react';
import { NetworkStatusType } from '../types/emergency';
import { getNetworkStatus, subscribeNetworkStatus } from '../services/network';

export function useNetworkStatus(): NetworkStatusType {
  const [status, setStatus] = useState<NetworkStatusType>(getNetworkStatus());

  useEffect(() => {
    const unsubscribe = subscribeNetworkStatus(setStatus);
    return unsubscribe;
  }, []);

  return status;
}
