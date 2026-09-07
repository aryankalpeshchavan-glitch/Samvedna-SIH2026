import React, { useState, useRef, useEffect } from 'react';
import { MapLayerMode, MapViewStyle, NeStateInfo, MonitoringPoint } from '../../types/map';
import { CitizenMapReport } from '../../types/emergency';
import { useTranslation } from '../../i18n/LanguageContext';
import { useClickOutside } from '../../hooks/useClickOutside';
import { Compass, RotateCcw, MapPin, X, Activity, Mountain, CloudRain, Droplets, Gauge, Sparkles, Navigation, Layers, HelpCircle, Globe, Check, ChevronDown } from 'lucide-react';

import { RiskZoneOut, classifyRiskLevel } from '../../types/api';

interface MapControlsOverlayProps {
  mapViewStyle?: MapViewStyle;
  onMapViewStyleChange?: (style: MapViewStyle) => void;
  layerMode: MapLayerMode;
  onLayerModeChange: (mode: MapLayerMode) => void;
  hoveredStateName: string | null;
  selectedState: NeStateInfo | null;
  selectedStation: MonitoringPoint | null;
  selectedCitizenReport: CitizenMapReport | null;
  selectedRiskZone?: RiskZoneOut | null;
  showSafeRoute: boolean;
  isEmergencyMode: boolean;
  onToggleEmergencyMode: () => void;
  onToggleSafeRoute: () => void;
  onOpenWhyRisk: () => void;
  onOpenTerrainScan: () => void;
  onOpenStoryMode: () => void;
  onMyAreaClick: () => void;
  onResetView: () => void;
  onCloseDetail: () => void;
}

export const MapControlsOverlay: React.FC<MapControlsOverlayProps> = ({
  mapViewStyle = 'satellite',
  onMapViewStyleChange,
  layerMode,
  onLayerModeChange,
  hoveredStateName,
  selectedState,
  selectedStation,
  selectedCitizenReport,
  selectedRiskZone,
  showSafeRoute,
  isEmergencyMode,
  onToggleEmergencyMode,
  onToggleSafeRoute,
  onOpenWhyRisk,
  onOpenTerrainScan,
  onOpenStoryMode,
  onMyAreaClick,
  onResetView,
  onCloseDetail,
}) => {
  const { t } = useTranslation();
  
  // Separate menu state for MAP VIEW (Top-Right) and RISK OVERLAYS (Bottom)
  const [showMapViewMenu, setShowMapViewMenu] = useState(false);
  const mapViewMenuRef = useRef<HTMLDivElement>(null);
  useClickOutside(mapViewMenuRef, () => setShowMapViewMenu(false), showMapViewMenu);

  const [showLayersMenu, setShowLayersMenu] = useState(false);
  const layersMenuRef = useRef<HTMLDivElement>(null);
  useClickOutside(layersMenuRef, () => setShowLayersMenu(false), showLayersMenu);

  // Close menus on Escape key
  useEffect(() => {
    if (!showMapViewMenu && !showLayersMenu) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowMapViewMenu(false);
        setShowLayersMenu(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showMapViewMenu, showLayersMenu]);

  return (
    <div className="absolute inset-0 pointer-events-none p-4 flex flex-col justify-between z-10 font-sans">
      {/* Top Floating Control Header Bar */}
      <div className="flex items-center justify-between pointer-events-auto">
        <div className="flex items-center space-x-2.5 bg-[#FAF9F3]/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-[#C7B89B]/50 shadow-sm">
          <Compass className="w-4 h-4 text-[#23483A] shrink-0" />
          <span className="font-heading text-xs font-bold text-[#202622] tracking-wide uppercase">
            {t('controls.regionHeader')}
          </span>
          <button
            onClick={onToggleEmergencyMode}
            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border transition-colors cursor-pointer ${
              isEmergencyMode
                ? 'bg-[#8E2F2B] text-[#FAF9F3] border-[#8E2F2B] animate-pulse'
                : 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/30 hover:bg-[#D88A32]/30'
            }`}
          >
            {isEmergencyMode ? t('controls.emergencyMode') : t('controls.watchMode')}
          </button>
        </div>

        {/* Top-Right Control Group: [ MAP VIEW ▾ ] [ STORY MODE ] [ RESET ] */}
        <div className="flex items-center space-x-2">
          {/* MAP VIEW SWITCHER POPOVER */}
          <div ref={mapViewMenuRef} className="relative">
            <button
              onClick={() => setShowMapViewMenu(!showMapViewMenu)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/90 backdrop-blur-md text-[#202622] border border-[#C7B89B]/50 hover:bg-[#E8E6DC] transition-colors shadow-sm cursor-pointer"
            >
              {mapViewStyle === 'satellite' ? (
                <Globe className="w-3.5 h-3.5 text-[#23483A]" />
              ) : (
                <Mountain className="w-3.5 h-3.5 text-[#A87C58]" />
              )}
              <span>{mapViewStyle === 'satellite' ? 'Satellite' : 'Terrain'}</span>
              <ChevronDown className="w-3 h-3 text-[#536A72]" />
            </button>

            {showMapViewMenu && (
              <div className="absolute top-full mt-1.5 right-0 w-44 bg-[#FAF9F3] border border-[#C7B89B] rounded-2xl shadow-xl p-2 z-50 text-xs font-mono font-sans space-y-1">
                <span className="text-[10px] font-heading font-bold uppercase text-[#536A72] block px-2 py-1 border-b border-[#C7B89B]/40">
                  MAP VIEW
                </span>
                <button
                  onClick={() => {
                    if (onMapViewStyleChange) onMapViewStyleChange('satellite');
                    setShowMapViewMenu(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                    mapViewStyle === 'satellite'
                      ? 'bg-[#23483A]/10 text-[#23483A] font-bold border border-[#23483A]/30'
                      : 'text-[#202622] hover:bg-[#E8E6DC]'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Globe className="w-3.5 h-3.5 text-[#23483A]" />
                    <span>Satellite</span>
                  </div>
                  {mapViewStyle === 'satellite' && <Check className="w-3.5 h-3.5 text-[#23483A]" />}
                </button>

                <button
                  onClick={() => {
                    if (onMapViewStyleChange) onMapViewStyleChange('terrain');
                    setShowMapViewMenu(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                    mapViewStyle === 'terrain'
                      ? 'bg-[#23483A]/10 text-[#23483A] font-bold border border-[#23483A]/30'
                      : 'text-[#202622] hover:bg-[#E8E6DC]'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <Mountain className="w-3.5 h-3.5 text-[#A87C58]" />
                    <span>Terrain (3D DEM)</span>
                  </div>
                  {mapViewStyle === 'terrain' && <Check className="w-3.5 h-3.5 text-[#23483A]" />}
                </button>
              </div>
            )}
          </div>

          <button
            onClick={onOpenStoryMode}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/90 backdrop-blur-md text-[#23483A] border border-[#23483A]/30 hover:bg-[#23483A] hover:text-[#FAF9F3] transition-colors shadow-sm cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{t('home.storyMode')}</span>
          </button>

          <button
            onClick={onResetView}
            className="p-2 rounded-xl bg-[#FAF9F3]/90 backdrop-blur-md text-[#202622] border border-[#C7B89B]/50 hover:bg-[#E8E6DC] transition-colors shadow-sm cursor-pointer"
            title={t('aria.resetCamera')}
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Hover Region Tag */}
      {hoveredStateName && !selectedState && !selectedStation && !selectedCitizenReport && (
        <div className="self-center pointer-events-auto bg-[#FAF9F3]/95 backdrop-blur-md px-4 py-1.5 rounded-full border border-[#C7B89B]/60 text-xs font-heading font-bold text-[#202622] shadow-md">
          {t('controls.regionTag')} <span className="text-[#23483A] font-serif-editorial text-sm font-normal italic">{hoveredStateName}</span>
        </div>
      )}

      {/* Selected State Detail Card Overlay */}
      {selectedState && (
        <div className="pointer-events-auto bg-[#FAF9F3]/95 backdrop-blur-md border border-[#C7B89B] rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E8E6DC]">
            <div className="flex items-center space-x-2">
              <Mountain className="w-5 h-5 text-[#A87C58]" />
              <div>
                <h4 className="text-base font-heading font-bold text-[#202622] uppercase tracking-wide">
                  {selectedState.name} ({selectedState.code})
                </h4>
                <span className="text-xs text-[#536A72]">{t('controls.capital')} {selectedState.capital}</span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-[#536A72] hover:text-[#202622] p-1" title={t('aria.closeDetail')}>
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[#536A72] text-[10px] block">{t('controls.rainfall24h')}</span>
              <strong className="text-[#23483A] text-sm">{selectedState.avgRainfall24h} mm</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[#536A72] text-[10px] block">{t('controls.soilMoisture')}</span>
              <strong className="text-[#D88A32] text-sm">{selectedState.avgSoilMoisture}%</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[#536A72] text-[10px] block">{t('controls.elevation')}</span>
              <strong className="text-[#202622] text-xs">{selectedState.elevationRange}</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[#536A72] text-[10px] block">{t('controls.landslideZones')}</span>
              <strong className="text-[#C6533C] text-sm">{selectedState.activeLandslideZones} {t('controls.active')}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Selected Monitoring Station Detail Card Overlay */}
      {selectedStation && (
        <div className="pointer-events-auto bg-[#FAF9F3]/95 backdrop-blur-md border border-[#C7B89B] rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E8E6DC]">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-[#23483A]" />
              <div>
                <h4 className="text-sm font-heading font-bold text-[#202622]">
                  {selectedStation.name}
                </h4>
                <span className="text-[11px] font-mono text-[#536A72]">ID: {selectedStation.id}</span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-[#536A72] hover:text-[#202622] p-1" title={t('aria.closeDetail')}>
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs font-mono text-center">
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <CloudRain className="w-4 h-4 text-[#536A72] mx-auto mb-1" />
              <span className="text-[10px] text-[#536A72] block">{t('controls.rainfall')}</span>
              <strong className="text-[#202622] text-xs">{selectedStation.rainfall24hMm} mm</strong>
            </div>
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <Droplets className="w-4 h-4 text-[#D88A32] mx-auto mb-1" />
              <span className="text-[10px] text-[#536A72] block">{t('controls.moisture')}</span>
              <strong className="text-[#202622] text-xs">{selectedStation.soilMoisturePct}%</strong>
            </div>
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <Gauge className="w-4 h-4 text-[#C6533C] mx-auto mb-1" />
              <span className="text-[10px] text-[#536A72] block">{t('controls.slope')}</span>
              <strong className="text-[#202622] text-xs">{selectedStation.slopeAngleDeg}°</strong>
            </div>
          </div>
        </div>
      )}

      {/* Selected Live ML Risk Zone Detail Card Overlay */}
      {selectedRiskZone && (
        <div className="pointer-events-auto bg-[#FAF9F3]/95 backdrop-blur-md border border-[#C7B89B] rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#E8E6DC]">
            <div className="flex items-center space-x-2">
              <Activity className={`w-5 h-5 ${classifyRiskLevel(selectedRiskZone.risk_score) === 'HIGH' ? 'text-[#C6533C]' : classifyRiskLevel(selectedRiskZone.risk_score) === 'MEDIUM' ? 'text-[#D88A32]' : 'text-[#23483A]'}`} />
              <div>
                <h4 className="text-sm font-heading font-bold text-[#202622]">
                  ML Risk Zone ({classifyRiskLevel(selectedRiskZone.risk_score)})
                </h4>
                <span className="text-[11px] font-mono text-[#536A72]">ID: {selectedRiskZone.id.slice(0, 8)}...</span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-[#536A72] hover:text-[#202622] p-1" title={t('aria.closeDetail')}>
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs font-mono text-center">
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[10px] text-[#536A72] block">Risk Score</span>
              <strong className={`text-xs ${classifyRiskLevel(selectedRiskZone.risk_score) === 'HIGH' ? 'text-[#C6533C]' : classifyRiskLevel(selectedRiskZone.risk_score) === 'MEDIUM' ? 'text-[#D88A32]' : 'text-[#23483A]'}`}>
                {(selectedRiskZone.risk_score * 100).toFixed(1)}%
              </strong>
            </div>
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[10px] text-[#536A72] block">Confidence</span>
              <strong className="text-[#23483A] text-xs">
                {((selectedRiskZone.confidence ?? 0.9) * 100).toFixed(1)}%
              </strong>
            </div>
            <div className="p-2 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
              <span className="text-[10px] text-[#536A72] block">Data Status</span>
              <strong className="text-[#202622] text-[10px] uppercase">
                {selectedRiskZone.data_status || selectedRiskZone.data_label || 'live'}
              </strong>
            </div>
          </div>

          <div className="text-[11px] font-mono text-[#536A72] space-y-1 bg-[#F4F1E8] p-2.5 rounded-xl border border-[#C7B89B]/40">
            <div>Coordinates: <span className="text-[#202622] font-bold">{selectedRiskZone.lat?.toFixed(4)}° N, {selectedRiskZone.lng?.toFixed(4)}° E</span></div>
            <div>Model: <span className="text-[#202622] font-bold">{selectedRiskZone.model_version || 'xgboost'}</span></div>
            <div>Computed: <span className="text-[#202622] font-bold">{new Date(selectedRiskZone.computed_at).toLocaleTimeString()}</span></div>
          </div>

          <button
            type="button"
            onClick={onOpenWhyRisk}
            className="w-full py-2 px-3 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#1b382d] transition-all cursor-pointer flex items-center justify-center space-x-1.5 shadow-sm"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Inspect Decision & Drivers</span>
          </button>
        </div>
      )}

      {/* Selected Citizen Map Report Detail Overlay */}
      {selectedCitizenReport && (
        <div className="pointer-events-auto bg-[#FAF9F3]/95 backdrop-blur-md border border-[#A87C58] rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-[#E8E6DC]">
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-[#C6533C]" />
              <div>
                <h4 className="text-sm font-heading font-bold text-[#202622]">
                  {selectedCitizenReport.title}
                </h4>
                <span className="text-[11px] font-mono text-[#536A72]">
                  {selectedCitizenReport.locationName} &bull; {selectedCitizenReport.reportedTimeAgo}
                </span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-[#536A72] hover:text-[#202622] p-1" title={t('aria.closeDetail')}>
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-[#202622] leading-relaxed font-medium">
            {selectedCitizenReport.description}
          </p>
          <div className="flex items-center justify-between text-[11px] font-mono pt-1">
            <span className="px-2 py-0.5 rounded bg-[#23483A]/10 text-[#23483A] font-bold">
              {t('controls.status')} {selectedCitizenReport.verifiedStatus}
            </span>
            <span className="text-[#C6533C] font-bold">{t('controls.severity')} {t(`severity.${selectedCitizenReport.severity}`)}</span>
          </div>
        </div>
      )}

      {/* Bottom Floating Interactive Toolbar & Risk Forecast Timeline */}
      <div className="pointer-events-auto space-y-3">
        {/* Floating Action Pills Bar */}
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto">
          <button
            onClick={onMyAreaClick}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/95 backdrop-blur-md text-[#202622] border border-[#C7B89B] hover:bg-[#23483A] hover:text-[#FAF9F3] transition-all shadow-sm cursor-pointer"
          >
            <Navigation className="w-3.5 h-3.5 text-[#23483A]" />
            <span>{t('home.myArea')}</span>
          </button>

          <button
            onClick={onOpenWhyRisk}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/95 backdrop-blur-md text-[#23483A] border border-[#23483A]/30 hover:bg-[#23483A] hover:text-[#FAF9F3] transition-all shadow-sm cursor-pointer"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>{t('home.whyRisk')}</span>
          </button>

          <button
            onClick={onOpenTerrainScan}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/95 backdrop-blur-md text-[#202622] border border-[#C7B89B] hover:bg-[#23483A] hover:text-[#FAF9F3] transition-all shadow-sm cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#A87C58]" />
            <span>{t('home.scanTerrain')}</span>
          </button>

          <button
            onClick={onToggleSafeRoute}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold transition-all shadow-sm cursor-pointer ${
              showSafeRoute
                ? 'bg-[#23483A] text-[#FAF9F3] border border-[#23483A]'
                : 'bg-[#FAF9F3]/95 backdrop-blur-md text-[#202622] border border-[#C7B89B] hover:bg-[#23483A] hover:text-[#FAF9F3]'
            }`}
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>{showSafeRoute ? t('home.hideSafeRoute') : t('home.showSafeRoute')}</span>
          </button>

          {/* DEDICATED RISK OVERLAYS MENU POPOVER */}
          <div ref={layersMenuRef} className="relative">
            <button
              onClick={() => setShowLayersMenu(!showLayersMenu)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-[#FAF9F3]/95 backdrop-blur-md text-[#202622] border border-[#C7B89B] hover:bg-[#E8E6DC] transition-all shadow-sm cursor-pointer"
            >
              <Layers className="w-3.5 h-3.5 text-[#23483A]" />
              <span>{t('home.layers')}: {layerMode.toUpperCase()}</span>
            </button>

            {showLayersMenu && (
              <div className="absolute bottom-full mb-2 right-0 w-48 bg-[#FAF9F3] border border-[#C7B89B] rounded-2xl shadow-2xl p-2.5 z-50 text-xs font-mono space-y-2 font-sans">
                <span className="text-[10px] font-heading font-bold uppercase text-[#536A72] block pb-1 border-b border-[#C7B89B]/40">
                  RISK OVERLAYS
                </span>
                <div className="space-y-1">
                  <button
                    onClick={() => {
                      onLayerModeChange(layerMode === 'risk' ? 'terrain' : 'risk');
                      setShowLayersMenu(false);
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                      layerMode === 'risk'
                        ? 'bg-[#23483A]/10 text-[#23483A] font-bold'
                        : 'text-[#202622] hover:bg-[#E8E6DC]'
                    }`}
                  >
                    <span>Risk Zones</span>
                    {layerMode === 'risk' && <Check className="w-3.5 h-3.5 text-[#23483A]" />}
                  </button>

                  <button
                    onClick={() => {
                      onLayerModeChange(layerMode === 'rainfall' ? 'risk' : 'rainfall');
                      setShowLayersMenu(false);
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors ${
                      layerMode === 'rainfall'
                        ? 'bg-[#536A72]/15 text-[#536A72] font-bold'
                        : 'text-[#202622] hover:bg-[#E8E6DC]'
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <CloudRain className="w-3.5 h-3.5 text-[#536A72]" />
                      <span>Rain Intensity</span>
                    </div>
                    {layerMode === 'rainfall' && <Check className="w-3.5 h-3.5 text-[#536A72]" />}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Regional 12h Scenario Outlook Timeline Bar */}
        <div className="bg-[#FAF9F3]/95 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-[#C7B89B]/60 shadow-md flex flex-wrap items-center justify-between gap-2.5 max-w-xl mx-auto text-xs font-mono text-[#202622]">
          <div className="flex items-center space-x-1.5 shrink-0">
            <span className="text-[#536A72] font-heading font-extrabold uppercase text-[11px] tracking-wider">
              REGIONAL 12H SCENARIO OUTLOOK
            </span>
            <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-[#D88A32]/15 text-[#965C22] border border-[#D88A32]/30">
              OUTLOOK
            </span>
          </div>
          <div className="flex items-center space-x-3 shrink-0">
            <span className="flex items-center space-x-1">
              <span className="text-[#536A72] font-medium">{t('controls.now')}</span>
              <strong className="px-2 py-0.5 rounded-md bg-[#23483A]/15 text-[#23483A] font-bold text-xs border border-[#23483A]/30">
                {t('severity.LOW')}
              </strong>
            </span>
            <span className="flex items-center space-x-1">
              <span className="text-[#536A72] font-medium">+3h:</span>
              <strong className="px-2 py-0.5 rounded-md bg-[#D88A32]/20 text-[#965C22] font-bold text-xs border border-[#D88A32]/40">
                {t('severity.WATCH')}
              </strong>
            </span>
            <span className="flex items-center space-x-1">
              <span className="text-[#536A72] font-medium">+6h:</span>
              <strong className="px-2 py-0.5 rounded-md bg-[#C6533C]/15 text-[#C6533C] font-bold text-xs border border-[#C6533C]/30">
                {t('severity.HIGH')}
              </strong>
            </span>
            <span className="flex items-center space-x-1">
              <span className="text-[#536A72] font-medium">+12h:</span>
              <strong className="px-2 py-0.5 rounded-md bg-[#C6533C]/15 text-[#C6533C] font-bold text-xs border border-[#C6533C]/30">
                {t('severity.HIGH')}
              </strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
