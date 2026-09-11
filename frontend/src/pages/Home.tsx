import React, { useRef, useEffect, useState } from 'react';
import { SosButton } from '../components/emergency/SosButton';
import { LocationData, NetworkStatusType, SosState, SosStatusDetail } from '../types/emergency';
import { SosStateViewer } from '../components/emergency/SosStateViewer';
import { animatePageEnter } from '../animations/pageTransitions';
import { TabType } from '../components/navigation/BottomNav';
import { NeMap3D } from '../components/map/NeMap3D';
import { MapControlsOverlay } from '../components/map/MapControlsOverlay';
import { MapLayerMode, MapViewStyle, NeStateInfo, MonitoringPoint } from '../types/map';
import { CitizenMapReport } from '../types/emergency';
import { WhyRiskModal } from '../components/interactive/WhyRiskModal';
import { TerrainScanner } from '../components/interactive/TerrainScanner';
import { SafeRouteOverlay } from '../components/interactive/SafeRouteOverlay';
import { StoryModeModal } from '../components/interactive/StoryModeModal';
import { EmergencyModeBanner } from '../components/emergency/EmergencyModeBanner';
import { PhoneCall, AlertOctagon, ShieldAlert, Loader2 } from 'lucide-react';
import { getRisk, getIncidents, getAuthInfo, AuthInfo, logout } from '../services/api';
import { RiskZoneOut, IncidentOut } from '../types/api';
import { useTranslation } from '../i18n/LanguageContext';

interface HomeProps {
  location: LocationData;
  refreshLocation: () => void;
  networkStatus: NetworkStatusType;
  sosState: SosState;
  statusDetail: SosStatusDetail;
  onTriggerSos: () => void;
  onResetSos: () => void;
  onNavigate: (tab: TabType) => void;
}

export const Home: React.FC<HomeProps> = ({
  location,
  refreshLocation,
  networkStatus,
  sosState,
  statusDetail,
  onTriggerSos,
  onResetSos,
  onNavigate: _onNavigate,
}) => {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);

  // Map View Style ('satellite' by default, optional 'terrain' CrisisCore view)
  const [mapViewStyle, setMapViewStyle] = useState<MapViewStyle>(() => {
    const saved = localStorage.getItem('samvedna_map_view_style');
    return saved === 'terrain' || saved === 'satellite' ? saved : 'satellite';
  });

  useEffect(() => {
    localStorage.setItem('samvedna_map_view_style', mapViewStyle);
  }, [mapViewStyle]);

  // Unified Operations Auth State
  const [authInfo, setAuthInfo] = useState<AuthInfo>(() => getAuthInfo());

  useEffect(() => {
    const handleAuthChange = () => {
      setAuthInfo(getAuthInfo());
    };
    window.addEventListener('crisiscore-auth-change', handleAuthChange);
    return () => window.removeEventListener('crisiscore-auth-change', handleAuthChange);
  }, []);

  // 3D Map & Interactive Modals State
  const [mapLayerMode, setMapLayerMode] = useState<MapLayerMode>('risk');
  const [selectedState, setSelectedState] = useState<NeStateInfo | null>(null);
  const [selectedStation, setSelectedStation] = useState<MonitoringPoint | null>(null);
  const [selectedCitizenReport, setSelectedCitizenReport] = useState<CitizenMapReport | null>(null);
  const [selectedRiskZone, setSelectedRiskZone] = useState<RiskZoneOut | null>(null);
  const [hoveredStateName, setHoveredStateName] = useState<string | null>(null);
  const [showSafeRoute, setShowSafeRoute] = useState(false);
  const [isEmergencyMode, setIsEmergencyMode] = useState(false);

  // Live Risk State
  const [riskZones, setRiskZones] = useState<RiskZoneOut[]>([]);
  const [isRiskLoading, setIsRiskLoading] = useState(false);
  const [riskError, setRiskError] = useState<string | null>(null);

  const fetchLiveRisk = async () => {
    const currentAuth = getAuthInfo();
    if (currentAuth.status !== 'authenticated') {
      setIsRiskLoading(false);
      setRiskError(null);
      setRiskZones([]);
      return;
    }

    setIsRiskLoading(true);
    setRiskError(null);
    try {
      const data = await getRisk(undefined, '24h', 2);
      if (Array.isArray(data)) {
        setRiskZones(data);
      } else {
        setRiskZones([]);
      }
    } catch (err: any) {
      console.error('[Home] Failed to fetch live risk data:', err);
      if (err?.status === 401) {
        setRiskError(null);
        setRiskZones([]);
      } else {
        setRiskError(err?.message || 'Live Risk Telemetry Unavailable');
      }
    } finally {
      setIsRiskLoading(false);
    }
  };

  // Live Incidents State
  const [incidents, setIncidents] = useState<IncidentOut[]>([]);
  const [isIncidentsLoading, setIsIncidentsLoading] = useState(false);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);

  const fetchLiveIncidents = async () => {
    const currentAuth = getAuthInfo();
    if (currentAuth.status !== 'authenticated') {
      setIsIncidentsLoading(false);
      setIncidentsError(null);
      setIncidents([]);
      return;
    }

    setIsIncidentsLoading(true);
    setIncidentsError(null);
    try {
      const data = await getIncidents(undefined, undefined, undefined, 2);
      if (Array.isArray(data)) {
        setIncidents(data);
      } else {
        setIncidents([]);
      }
    } catch (err: any) {
      console.warn('[Home] Failed to fetch live incidents:', err);
      if (err?.status === 401) {
        setIncidentsError(null);
        setIncidents([]);
      } else {
        setIncidentsError(err?.message || 'Live Incident Telemetry Unavailable');
      }
    } finally {
      setIsIncidentsLoading(false);
    }
  };

  // Immediate First-Load Data Initialization on Authentication
  useEffect(() => {
    if (authInfo.status === 'authenticated') {
      fetchLiveRisk();
      fetchLiveIncidents();
    } else {
      setRiskZones([]);
      setIncidents([]);
      setRiskError(null);
      setIncidentsError(null);
      setIsRiskLoading(false);
      setIsIncidentsLoading(false);
    }
  }, [authInfo.status]);

  // Periodic Telemetry Refresh (Only when authenticated)
  useEffect(() => {
    if (authInfo.status !== 'authenticated') return;
    const handleRefresh = () => {
      fetchLiveRisk();
      fetchLiveIncidents();
    };
    window.addEventListener('crisiscore-refresh-telemetry', handleRefresh);
    const interval = setInterval(handleRefresh, 15000);
    return () => {
      window.removeEventListener('crisiscore-refresh-telemetry', handleRefresh);
      clearInterval(interval);
    };
  }, [authInfo.status]);

  // Interactive Explainer Modals
  const [isWhyRiskOpen, setIsWhyRiskOpen] = useState(false);
  const [isTerrainScanOpen, setIsTerrainScanOpen] = useState(false);
  const [isStoryModeOpen, setIsStoryModeOpen] = useState(false);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const handleResetMapCamera = () => {
    setSelectedState(null);
    setSelectedStation(null);
    setSelectedCitizenReport(null);
    setSelectedRiskZone(null);
    setShowSafeRoute(false);
  };

  const handleMyAreaClick = () => {
    refreshLocation();
    setSelectedState(null);
    setSelectedStation(null);
    setSelectedCitizenReport(null);
    setSelectedRiskZone(null);
  };

  const userLngLat: [number, number] | null =
    location.longitude && location.latitude ? [location.longitude, location.latitude] : [91.7362, 26.1445];

  return (
    <div ref={containerRef} className="pb-16 lg:pb-4 font-sans space-y-3">
      
      {/* High-Stress Emergency Mode Evacuation Banner (Active when toggled or critical warning) */}
      {isEmergencyMode && (
        <div className="max-w-xl mx-auto px-2">
          <EmergencyModeBanner
            onShowRoute={() => setShowSafeRoute(true)}
            onExitEmergencyMode={() => setIsEmergencyMode(false)}
          />
        </div>
      )}

      {/* Operations Access Barrier for Citizen Tokens */}
      {authInfo.status === 'access_required' && (
        <div className="max-w-xl mx-auto p-3.5 rounded-2xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-[#8E2F2B] font-mono text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 shadow-sm">
          <div className="flex items-center space-x-2.5">
            <AlertOctagon className="w-5 h-5 shrink-0 text-[#8E2F2B]" />
            <div>
              <strong className="block font-heading text-sm uppercase">Operations Access Required</strong>
              <span className="text-[11px] text-[#8E2F2B]/90">
                Citizen session active. Live tactical risk and incident telemetry require Officer or Admin authorization.
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-2 shrink-0 w-full sm:w-auto justify-end">
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('open-operations-auth'))}
              className="px-3 py-1.5 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#1b382d] transition-all cursor-pointer"
            >
              Sign In as Officer
            </button>
            <button
              onClick={() => logout()}
              className="px-2.5 py-1.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B] text-[#8E2F2B] text-xs font-mono font-bold hover:bg-[#E8E6DC] transition-all cursor-pointer"
            >
              Log Out
            </button>
          </div>
        </div>
      )}

      {/* Operations Login Banner when Unauthenticated */}
      {authInfo.status === 'unauthenticated' && (
        <div className="max-w-xl mx-auto p-3 rounded-2xl bg-[#23483A]/10 border border-[#23483A]/30 text-[#23483A] font-mono text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 shrink-0 text-[#23483A]" />
            <span>Tactical Command Interface: Please authenticate as Officer or Admin.</span>
          </div>
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('open-operations-auth'))}
            className="px-3 py-1 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#1b382d] transition-all cursor-pointer shrink-0 ml-2"
          >
            Log In
          </button>
        </div>
      )}

      {/* Initializing Session State */}
      {authInfo.status === 'bootstrapping' && (
        <div className="max-w-xl mx-auto p-2.5 rounded-2xl bg-[#23483A]/10 border border-[#23483A]/30 text-[#23483A] font-mono text-xs flex items-center justify-center space-x-2 shadow-sm">
          <Loader2 className="w-4 h-4 animate-spin text-[#23483A]" />
          <span>Initializing Operations Command Session...</span>
        </div>
      )}

      {/* 90% Viewport Hero Map Section — THE MAP IS THE HERO */}
      <div className="relative rounded-2xl overflow-hidden shadow-lg border border-[#C7B89B]/50 bg-[#F4F1E8]">
        <NeMap3D
          authStatus={authInfo.status}
          mapViewStyle={mapViewStyle}
          layerMode={mapLayerMode}
          selectedState={selectedState}
          selectedStation={selectedStation}
          selectedCitizenReport={selectedCitizenReport}
          selectedRiskZone={selectedRiskZone}
          riskZones={riskZones}
          isRiskLoading={isRiskLoading}
          riskError={riskError}
          onRetryRisk={fetchLiveRisk}
          incidents={incidents}
          isIncidentsLoading={isIncidentsLoading}
          incidentError={incidentsError}
          onRetryIncidents={fetchLiveIncidents}
          showSafeRoute={showSafeRoute}
          userLocation={userLngLat}
          onSelectState={setSelectedState}
          onSelectStation={setSelectedStation}
          onSelectCitizenReport={setSelectedCitizenReport}
          onSelectRiskZone={setSelectedRiskZone}
          onHoverState={setHoveredStateName}
        />

        <MapControlsOverlay
          mapViewStyle={mapViewStyle}
          onMapViewStyleChange={setMapViewStyle}
          layerMode={mapLayerMode}
          onLayerModeChange={setMapLayerMode}
          hoveredStateName={hoveredStateName}
          selectedState={selectedState}
          selectedStation={selectedStation}
          selectedCitizenReport={selectedCitizenReport}
          selectedRiskZone={selectedRiskZone}
          showSafeRoute={showSafeRoute}
          isEmergencyMode={isEmergencyMode}
          onToggleEmergencyMode={() => setIsEmergencyMode(!isEmergencyMode)}
          onToggleSafeRoute={() => setShowSafeRoute(!showSafeRoute)}
          onOpenWhyRisk={() => setIsWhyRiskOpen(true)}
          onOpenTerrainScan={() => setIsTerrainScanOpen(true)}
          onOpenStoryMode={() => setIsStoryModeOpen(true)}
          onMyAreaClick={handleMyAreaClick}
          onResetView={handleResetMapCamera}
          onCloseDetail={() => {
            setSelectedState(null);
            setSelectedStation(null);
            setSelectedCitizenReport(null);
            setSelectedRiskZone(null);
          }}
        />

        {/* Safe Route Info Drawer Overlay */}
        <SafeRouteOverlay isOpen={showSafeRoute} onClose={() => setShowSafeRoute(false)} />
      </div>

      {/* Floating Light SOS Action Trigger Bar sitting neatly below Hero Map */}
      <div className="max-w-xl mx-auto px-2">
        {sosState !== 'IDLE' ? (
          <SosStateViewer statusDetail={statusDetail} onReset={onResetSos} />
        ) : (
          <SosButton onTrigger={onTriggerSos} />
        )}
      </div>

      {/* Feature Phone / SMS Fallback Banner */}
      <div className="max-w-xl mx-auto p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/40 text-xs text-[#536A72] flex items-center justify-between font-mono shadow-sm">
        <div className="flex items-center space-x-2">
          <PhoneCall className="w-4 h-4 text-[#23483A]" />
          <span>{t('fallback.smsFallback')} <strong className="text-[#202622]">{t('fallback.smsAction')}</strong></span>
        </div>
        <span className="text-[10px] text-[#23483A] font-bold">{t('fallback.featurePhonesReady')}</span>
      </div>

      {networkStatus === 'OFFLINE' && (
        <div className="max-w-xl mx-auto p-3 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-xs text-[#8E2F2B] font-mono flex items-center space-x-2">
          <AlertOctagon className="w-4 h-4 shrink-0" />
          <span>{t('fallback.offlineWarning')}</span>
        </div>
      )}

      {/* Interactive Modals */}
      <WhyRiskModal
        isOpen={isWhyRiskOpen}
        onClose={() => setIsWhyRiskOpen(false)}
        onShowRoute={() => setShowSafeRoute(true)}
        lat={selectedRiskZone?.lat ?? selectedStation?.lat ?? (location.latitude || 26.1445)}
        lng={selectedRiskZone?.lng ?? selectedStation?.lng ?? (location.longitude || 91.7362)}
        zoneId={selectedRiskZone?.id}
        locationName={
          selectedRiskZone
            ? `Risk Zone (${selectedRiskZone.id.slice(0, 8)}...)`
            : (selectedStation?.name ?? selectedState?.name ?? 'My Current Location')
        }
      />

      <TerrainScanner
        isOpen={isTerrainScanOpen}
        onClose={() => setIsTerrainScanOpen(false)}
      />

      <StoryModeModal
        isOpen={isStoryModeOpen}
        onClose={() => setIsStoryModeOpen(false)}
      />
    </div>
  );
};
