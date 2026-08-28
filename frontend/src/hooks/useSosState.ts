import { useState, useCallback } from 'react';
import { SosState, SosPayload, IncidentCategory, SosStatusDetail } from '../types/emergency';
import { getCurrentLocation } from '../services/location';
import { savePendingAction } from '../services/offlineStorage';
import { getNetworkStatus } from '../services/network';

export function useSosState() {
  const [sosState, setSosState] = useState<SosState>('IDLE');
  const [currentSos, setCurrentSos] = useState<SosPayload | null>(null);
  const [statusDetail, setStatusDetail] = useState<SosStatusDetail>({ state: 'IDLE' });

  // Initiate confirmation step
  const initiateSos = useCallback(() => {
    setSosState('SOS_CONFIRMATION');
    setStatusDetail({ state: 'SOS_CONFIRMATION' });
  }, []);

  // Cancel confirmation step
  const cancelSos = useCallback(() => {
    setSosState('IDLE');
    setStatusDetail({ state: 'IDLE' });
  }, []);

  // Confirm emergency trigger
  const confirmAndTriggerSos = useCallback(async (incidentCategory?: IncidentCategory, note?: string) => {
    setSosState('SENDING');
    setStatusDetail({ state: 'SENDING' });

    const location = await getCurrentLocation();
    const network = getNetworkStatus();
    const sosId = `SOS-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`;

    const payload: SosPayload = {
      sosId,
      timestamp: Date.now(),
      location,
      incidentType: incidentCategory,
      note,
      networkStatusOnTrigger: network,
      dataSource: 'synthetic', // Clear explicit label for Day 1 mock
    };

    setCurrentSos(payload);

    // Simulate network delay / decision logic
    setTimeout(async () => {
      if (network === 'OFFLINE') {
        // Save to IndexedDB queue
        await savePendingAction('SOS', payload);
        setSosState('OFFLINE_QUEUED');
        setStatusDetail({
          state: 'OFFLINE_QUEUED',
          sosId: payload.sosId,
          timestamp: payload.timestamp,
          errorMessage: 'No active connection. Emergency signal saved locally and queued for automatic sync.',
        });
      } else {
        // Mock sending success (with simulated future state transitions for testing)
        setSosState('SENT');
        setStatusDetail({
          state: 'SENT',
          sosId: payload.sosId,
          timestamp: payload.timestamp,
          lastUpdatedText: 'Signal transmitted to CrisisCore Emergency Relay',
        });

        // Demo simulation: Auto-advance after 5s to VERIFIED -> ASSIGNED for preview
        setTimeout(() => {
          setStatusDetail({
            state: 'VERIFIED',
            sosId: payload.sosId,
            timestamp: payload.timestamp,
            lastUpdatedText: 'Verified by Emergency Operator',
          });
          setSosState('VERIFIED');
        }, 5000);

        setTimeout(() => {
          setStatusDetail({
            state: 'VOLUNTEER_EN_ROUTE',
            sosId: payload.sosId,
            timestamp: payload.timestamp,
            assignedVolunteerName: 'Alex Kumar (NDRF Certified)',
            assignedVolunteerPhone: '+91 98765 43210',
            etaMinutes: 12,
            lastUpdatedText: 'Volunteer dispatched to your detected coordinates',
          });
          setSosState('VOLUNTEER_EN_ROUTE');
        }, 12000);
      }
    }, 1200);
  }, []);

  const resetSos = useCallback(() => {
    setSosState('IDLE');
    setCurrentSos(null);
    setStatusDetail({ state: 'IDLE' });
  }, []);

  return {
    sosState,
    currentSos,
    statusDetail,
    initiateSos,
    cancelSos,
    confirmAndTriggerSos,
    resetSos,
    setSosState, // Allowed for state simulation / switching
  };
}
