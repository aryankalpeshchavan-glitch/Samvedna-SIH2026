import { useState, useCallback } from 'react';
import { SosState, SosPayload, IncidentCategory, SeverityLevel, SosStatusDetail } from '../types/emergency';
import { getCurrentLocation } from '../services/location';
import { savePendingAction } from '../services/offlineStorage';
import { getNetworkStatus } from '../services/network';
import { createIncident, getStatus } from '../services/api';
import { mapCategoryToBackendType, mapSeverityToInteger } from '../types/api';

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
  const confirmAndTriggerSos = useCallback(async (incidentCategory?: IncidentCategory, note?: string, severity?: SeverityLevel) => {
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
      dataSource: 'live',
    };

    setCurrentSos(payload);

    // Give UI 300ms for tactile feedback before dispatching
    setTimeout(async () => {
      if (network === 'OFFLINE') {
        // Save to IndexedDB queue
        await savePendingAction('SOS', payload);
        setSosState('OFFLINE_QUEUED');
        setStatusDetail({
          state: 'OFFLINE_QUEUED',
          sosId: payload.sosId,
          timestamp: payload.timestamp,
          errorMessage: 'No active network connection. Emergency report saved locally and queued for automatic transmission.',
        });
      } else {
        // Try real backend
        try {
          const lat = location.latitude ?? 26.14;
          const lng = location.longitude ?? 91.73;
          const backendType = mapCategoryToBackendType(incidentCategory);
          const intSeverity = mapSeverityToInteger(severity ?? 'HIGH');

          // Preserve original specific category in description if mapped
          const formattedDesc = incidentCategory && incidentCategory.toLowerCase() !== backendType
            ? `[Category: ${incidentCategory}] ${note || `Emergency SOS ${payload.sosId}`}`
            : (note || `Emergency SOS ${payload.sosId}`);

          const res = await createIncident({
            type: backendType,
            description: formattedDesc,
            lat,
            lng,
            severity: intSeverity,
            idempotency_key: payload.sosId,
          });

          setSosState('SENT');
          setStatusDetail({
            state: 'SENT',
            sosId: res.id || payload.sosId,
            timestamp: payload.timestamp,
            lastUpdatedText: `Signal transmitted — Incident #${res.id || payload.sosId} registered`,
          });

          // Poll real authenticated status endpoint for verification & volunteer dispatch
          let attempts = 0;
          const poll = setInterval(async () => {
            try {
              const st = await getStatus(res.id);
              if (st && (st.status === 'verified' || st.status === 'assigned')) {
                if (st.status === 'verified' && !st.assignment) {
                  setStatusDetail((prev) => ({
                    ...prev,
                    state: 'VERIFIED',
                    sosId: res.id,
                    lastUpdatedText: 'Incident verified by emergency operator',
                  }));
                  setSosState('VERIFIED');
                }
                if (st.assignment) {
                  setStatusDetail((prev) => ({
                    ...prev,
                    state: 'VOLUNTEER_EN_ROUTE',
                    sosId: res.id,
                    assignedVolunteerName: `Responder #${st.assignment?.volunteer_id}`,
                    lastUpdatedText: `Responder #${st.assignment?.volunteer_id} assigned (Status: ${st.assignment?.status})`,
                  }));
                  setSosState('VOLUNTEER_EN_ROUTE');
                  clearInterval(poll);
                }
              }
            } catch (pollErr: any) {
              console.warn('[SOS] Status poll error:', pollErr);
              if (pollErr?.message?.includes('401')) {
                setStatusDetail((prev) => ({
                  ...prev,
                  state: 'ERROR',
                  errorMessage: 'Authentication expired during status check. Please sign in again.',
                }));
                setSosState('ERROR');
                clearInterval(poll);
              }
            }
            if (++attempts > 40) clearInterval(poll);
          }, 3000);
        } catch (e: any) {
          // Surface actual error to UI instead of fake success
          console.error('[SOS] Backend transmission failed:', e);
          setSosState('ERROR');
          setStatusDetail({
            state: 'ERROR',
            sosId: payload.sosId,
            timestamp: payload.timestamp,
            errorMessage: `Transmission failed: ${e?.message || 'Could not connect to CrisisCore backend.'}`,
          });
        }
      }
    }, 300);
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
