import React from 'react';
import { MapLayerMode, NeStateInfo, MonitoringPoint } from '../../types/map';
import { CitizenMapReport } from '../../types/emergency';
import { useTranslation } from '../../i18n/LanguageContext';
import { Compass, RotateCcw, MapPin, X, Activity, Mountain, CloudRain, Droplets, Gauge, Sparkles, Navigation, Layers, HelpCircle } from 'lucide-react';

interface MapControlsOverlayProps {
  layerMode: MapLayerMode;
  onLayerModeChange: (mode: MapLayerMode) => void;
  hoveredStateName: string | null;
  selectedState: NeStateInfo | null;
  selectedStation: MonitoringPoint | null;
  selectedCitizenReport: CitizenMapReport | null;
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
  layerMode,
  onLayerModeChange,
  hoveredStateName,
  selectedState,
  selectedStation,
  selectedCitizenReport,
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

        <div className="flex items-center space-x-2">
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

          <button
            onClick={() => {
              if (layerMode === 'terrain') onLayerModeChange('risk');
              else if (layerMode === 'risk') onLayerModeChange('rainfall');
              else onLayerModeChange('terrain');
            }}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold transition-all shadow-sm cursor-pointer ${
              layerMode === 'rainfall'
                ? 'bg-[#536A72] text-[#FAF9F3] border border-[#536A72]'
                : 'bg-[#FAF9F3]/95 backdrop-blur-md text-[#202622] border border-[#C7B89B] hover:bg-[#E8E6DC]'
            }`}
          >
            {layerMode === 'rainfall' ? (
              <CloudRain className="w-3.5 h-3.5 text-[#FAF9F3]" />
            ) : (
              <Layers className="w-3.5 h-3.5 text-[#536A72]" />
            )}
            <span>{t('home.layers')}: {layerMode.toUpperCase()}</span>
          </button>
        </div>

        {/* Risk Forecast Timeline Bar */}
        <div className="bg-[#FAF9F3]/90 backdrop-blur-md px-4 py-2 rounded-xl border border-[#C7B89B]/50 flex items-center justify-between max-w-xl mx-auto text-xs font-mono shadow-sm">
          <span className="text-[#536A72] font-heading font-bold uppercase text-[10px]">{t('controls.riskForecast')}</span>
          <div className="flex items-center space-x-4">
            <span>{t('controls.now')} <strong className="text-[#23483A]">{t('severity.LOW')}</strong></span>
            <span>+3h: <strong className="text-[#D88A32]">{t('severity.WATCH')}</strong></span>
            <span>+6h: <strong className="text-[#C6533C]">{t('severity.HIGH')}</strong></span>
            <span>+12h: <strong className="text-[#C6533C]">{t('severity.HIGH')}</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
