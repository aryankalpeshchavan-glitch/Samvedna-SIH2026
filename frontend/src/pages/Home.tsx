import React, { useRef, useEffect, useState } from 'react';
import { SosButton } from '../components/emergency/SosButton';
import { LocationData, NetworkStatusType, SosState, SosStatusDetail } from '../types/emergency';
import { SosStateViewer } from '../components/emergency/SosStateViewer';
import { animatePageEnter } from '../animations/pageTransitions';
import { TabType } from '../components/navigation/BottomNav';
import { NeMap3D } from '../components/map/NeMap3D';
import { MapControlsOverlay } from '../components/map/MapControlsOverlay';
import { MapLayerMode, NeStateInfo, MonitoringPoint } from '../types/map';
import { CitizenMapReport } from '../types/emergency';
import { WhyRiskModal } from '../components/interactive/WhyRiskModal';
import { TerrainScanner } from '../components/interactive/TerrainScanner';
import { SafeRouteOverlay } from '../components/interactive/SafeRouteOverlay';
import { StoryModeModal } from '../components/interactive/StoryModeModal';
import { PhoneCall, AlertOctagon } from 'lucide-react';

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
  const containerRef = useRef<HTMLDivElement>(null);

  // 3D Map & Interactive Modals State
  const [mapLayerMode, setMapLayerMode] = useState<MapLayerMode>('terrain');
  const [selectedState, setSelectedState] = useState<NeStateInfo | null>(null);
  const [selectedStation, setSelectedStation] = useState<MonitoringPoint | null>(null);
  const [selectedCitizenReport, setSelectedCitizenReport] = useState<CitizenMapReport | null>(null);
  const [hoveredStateName, setHoveredStateName] = useState<string | null>(null);
  const [showSafeRoute, setShowSafeRoute] = useState(false);

  // Interactive Explainer Modals
  const [isWhyRiskOpen, setIsWhyRiskOpen] = useState(false);
  const [isTerrainScanOpen, setIsTerrainScanOpen] = useState(false);
  const [isStoryModeOpen, setIsStoryModeOpen] = useState(false);
  const [centerUserLocationTrigger, setCenterUserLocationTrigger] = useState(0);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const handleResetMapCamera = () => {
    setSelectedState(null);
    setSelectedStation(null);
    setSelectedCitizenReport(null);
    setShowSafeRoute(false);
  };

  const handleMyAreaClick = async () => {
    setSelectedState(null);
    setSelectedStation(null);
    await refreshLocation();
    setCenterUserLocationTrigger(Date.now());
  };

  const userLngLat: [number, number] | null =
    location.longitude && location.latitude ? [location.longitude, location.latitude] : [91.7362, 26.1445];

  return (
    <div className="font-sans">
      
      {/* Full Viewport Background Map Section */}
      <div className="fixed inset-0 z-0 bg-main">
        <NeMap3D
          layerMode={mapLayerMode}
          selectedState={selectedState}
          selectedStation={selectedStation}
          selectedCitizenReport={selectedCitizenReport}
          showSafeRoute={showSafeRoute}
          userLocation={userLngLat}
          centerUserLocationTrigger={centerUserLocationTrigger}
          onSelectState={setSelectedState}
          onSelectStation={setSelectedStation}
          onSelectCitizenReport={setSelectedCitizenReport}
          onHoverState={setHoveredStateName}
        />

        <MapControlsOverlay
          layerMode={mapLayerMode}
          onLayerModeChange={setMapLayerMode}
          hoveredStateName={hoveredStateName}
          selectedState={selectedState}
          selectedStation={selectedStation}
          selectedCitizenReport={selectedCitizenReport}
          showSafeRoute={showSafeRoute}
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
          }}
        />

        {/* Safe Route Info Drawer Overlay */}
        <SafeRouteOverlay isOpen={showSafeRoute} onClose={() => setShowSafeRoute(false)} />
      </div>

      {/* Floating Bottom Action Trigger Bar */}
      <div ref={containerRef} className="fixed bottom-0 inset-x-0 z-20 pointer-events-none pb-20 lg:pb-6 px-4 space-y-3 flex flex-col items-center">
        <div className="w-full max-w-xl mx-auto pointer-events-auto">
          {sosState !== 'IDLE' ? (
            <SosStateViewer statusDetail={statusDetail} onReset={onResetSos} />
          ) : (
            <SosButton onTrigger={onTriggerSos} />
          )}
        </div>

        {/* Feature Phone / SMS Fallback Banner */}
        <div className="w-full max-w-xl mx-auto p-3 rounded-xl bg-surface border border-border/40 text-xs text-muted flex items-center justify-between font-mono shadow-sm pointer-events-auto">
          <div className="flex items-center space-x-2">
            <PhoneCall className="w-4 h-4 text-accent" />
            <span>SMS Fallback: <strong className="text-primary">SMS 'SOS' to 56161</strong></span>
          </div>
          <span className="text-[10px] text-accent font-bold">Feature Phones Ready</span>
        </div>

        {networkStatus === 'OFFLINE' && (
          <div className="w-full max-w-xl mx-auto p-3 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-xs text-[#8E2F2B] font-mono flex items-center space-x-2 pointer-events-auto">
            <AlertOctagon className="w-4 h-4 shrink-0" />
            <span>⚠️ OFFLINE MODE: SOS request saved in IndexedDB; will auto-sync on reconnect.</span>
          </div>
        )}
      </div>

      {/* Interactive Modals */}
      <WhyRiskModal
        isOpen={isWhyRiskOpen}
        onClose={() => setIsWhyRiskOpen(false)}
        onShowRoute={() => setShowSafeRoute(true)}
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
