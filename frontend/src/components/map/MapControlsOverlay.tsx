import React from 'react';
import { MapLayerMode, NeStateInfo, MonitoringPoint } from '../../types/map';
import { CitizenMapReport } from '../../types/emergency';
import { Compass, RotateCcw, MapPin, X, Activity, Mountain, CloudRain, Droplets, Gauge, ShieldAlert, Sparkles, Navigation, Layers, HelpCircle } from 'lucide-react';

interface MapControlsOverlayProps {
  layerMode: MapLayerMode;
  onLayerModeChange: (mode: MapLayerMode) => void;
  hoveredStateName: string | null;
  selectedState: NeStateInfo | null;
  selectedStation: MonitoringPoint | null;
  selectedCitizenReport: CitizenMapReport | null;
  showSafeRoute: boolean;
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
  onToggleSafeRoute,
  onOpenWhyRisk,
  onOpenTerrainScan,
  onOpenStoryMode,
  onMyAreaClick,
  onResetView,
  onCloseDetail,
}) => {
  return (
    <div className="absolute inset-0 pointer-events-none p-4 pt-24 pb-64 lg:pb-48 flex flex-col justify-between z-10 font-sans">
      {/* Top Floating Control Header Bar */}
      <div className="flex items-center justify-between pointer-events-auto">
        <div className="flex items-center space-x-2.5 bg-surface/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-border/50 shadow-sm">
          <Compass className="w-4 h-4 text-accent shrink-0" />
          <span className="font-heading text-xs font-bold text-primary tracking-wide uppercase">
            NORTH EASTERN REGION
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#D88A32]/15 text-[#D88A32] border border-[#D88A32]/30">
            WATCH
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenStoryMode}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-heading font-bold bg-surface/90 backdrop-blur-md text-accent border border-accent/30 hover:bg-accent hover:text-surface transition-colors shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Story Mode</span>
          </button>

          <button
            onClick={onResetView}
            className="p-2 rounded-xl bg-surface/90 backdrop-blur-md text-primary border border-border/50 hover:bg-hover transition-colors shadow-sm"
            title="Reset Camera View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Hover Region Tag */}
      {hoveredStateName && !selectedState && !selectedStation && !selectedCitizenReport && (
        <div className="self-center pointer-events-auto bg-surface/95 backdrop-blur-md px-4 py-1.5 rounded-full border border-border/60 text-xs font-heading font-bold text-primary shadow-md">
          Region: <span className="text-accent font-serif-editorial text-sm font-normal italic">{hoveredStateName}</span>
        </div>
      )}

      {/* Selected State Detail Card Overlay */}
      {selectedState && (
        <div className="pointer-events-auto bg-surface/95 backdrop-blur-md border border-border rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-hover">
            <div className="flex items-center space-x-2">
              <Mountain className="w-5 h-5 text-border" />
              <div>
                <h4 className="text-base font-heading font-bold text-primary uppercase tracking-wide">
                  {selectedState.name} ({selectedState.code})
                </h4>
                <span className="text-xs text-muted">Capital: {selectedState.capital}</span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-muted hover:text-primary p-1">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2.5 rounded-xl bg-main border border-border/40">
              <span className="text-muted text-[10px] block">24H RAINFALL</span>
              <strong className="text-accent text-sm">{selectedState.avgRainfall24h} mm</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-main border border-border/40">
              <span className="text-muted text-[10px] block">SOIL MOISTURE</span>
              <strong className="text-[#D88A32] text-sm">{selectedState.avgSoilMoisture}%</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-main border border-border/40">
              <span className="text-muted text-[10px] block">ELEVATION</span>
              <strong className="text-primary text-xs">{selectedState.elevationRange}</strong>
            </div>
            <div className="p-2.5 rounded-xl bg-main border border-border/40">
              <span className="text-muted text-[10px] block">LANDSLIDE ZONES</span>
              <strong className="text-[#C6533C] text-sm">{selectedState.activeLandslideZones} Active</strong>
            </div>
          </div>
        </div>
      )}

      {/* Selected Monitoring Station Detail Card Overlay */}
      {selectedStation && (
        <div className="pointer-events-auto bg-surface/95 backdrop-blur-md border border-border rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-hover">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-accent" />
              <div>
                <h4 className="text-sm font-heading font-bold text-primary">
                  {selectedStation.name}
                </h4>
                <span className="text-[11px] font-mono text-muted">ID: {selectedStation.id}</span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-muted hover:text-primary p-1">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs font-mono text-center">
            <div className="p-2 rounded-xl bg-main border border-border/40">
              <CloudRain className="w-4 h-4 text-muted mx-auto mb-1" />
              <span className="text-[10px] text-muted block">Rainfall</span>
              <strong className="text-primary text-xs">{selectedStation.rainfall24hMm} mm</strong>
            </div>
            <div className="p-2 rounded-xl bg-main border border-border/40">
              <Droplets className="w-4 h-4 text-[#D88A32] mx-auto mb-1" />
              <span className="text-[10px] text-muted block">Moisture</span>
              <strong className="text-primary text-xs">{selectedStation.soilMoisturePct}%</strong>
            </div>
            <div className="p-2 rounded-xl bg-main border border-border/40">
              <Gauge className="w-4 h-4 text-[#C6533C] mx-auto mb-1" />
              <span className="text-[10px] text-muted block">Slope</span>
              <strong className="text-primary text-xs">{selectedStation.slopeAngleDeg}°</strong>
            </div>
          </div>
        </div>
      )}

      {/* Selected Citizen Map Report Detail Overlay */}
      {selectedCitizenReport && (
        <div className="pointer-events-auto bg-surface/95 backdrop-blur-md border border-border rounded-2xl p-4 shadow-xl max-w-sm w-full space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-hover">
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-[#C6533C]" />
              <div>
                <h4 className="text-sm font-heading font-bold text-primary">
                  {selectedCitizenReport.title}
                </h4>
                <span className="text-[11px] font-mono text-muted">
                  {selectedCitizenReport.locationName} &bull; {selectedCitizenReport.reportedTimeAgo}
                </span>
              </div>
            </div>
            <button onClick={onCloseDetail} className="text-muted hover:text-primary p-1">
              <X className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-primary leading-relaxed font-medium">
            {selectedCitizenReport.description}
          </p>
          <div className="flex items-center justify-between text-[11px] font-mono pt-1">
            <span className="px-2 py-0.5 rounded bg-accent/10 text-accent font-bold">
              Status: {selectedCitizenReport.verifiedStatus}
            </span>
            <span className="text-[#C6533C] font-bold">Severity: {selectedCitizenReport.severity}</span>
          </div>
        </div>
      )}

      {/* Bottom Floating Interactive Toolbar & Risk Forecast Timeline */}
      <div className="pointer-events-auto space-y-3">
        {/* Floating Action Pills Bar */}
        <div className="flex flex-wrap items-center justify-center gap-2 max-w-2xl mx-auto">
          <button
            onClick={onMyAreaClick}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-surface/95 backdrop-blur-md text-primary border border-border hover:bg-accent hover:text-surface transition-all shadow-sm"
          >
            <Navigation className="w-3.5 h-3.5 text-accent" />
            <span>MY AREA</span>
          </button>

          <button
            onClick={onOpenWhyRisk}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-surface/95 backdrop-blur-md text-accent border border-accent/30 hover:bg-accent hover:text-surface transition-all shadow-sm"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>WHY IS MY AREA AT RISK?</span>
          </button>

          <button
            onClick={onOpenTerrainScan}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-surface/95 backdrop-blur-md text-primary border border-border hover:bg-accent hover:text-surface transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5 text-border" />
            <span>SCAN TERRAIN</span>
          </button>

          <button
            onClick={onToggleSafeRoute}
            className={`flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold transition-all shadow-sm ${
              showSafeRoute
                ? 'bg-accent text-surface border border-accent'
                : 'bg-surface/95 backdrop-blur-md text-primary border border-border hover:bg-accent hover:text-surface'
            }`}
          >
            <Navigation className="w-3.5 h-3.5" />
            <span>{showSafeRoute ? 'HIDE SAFE ROUTE' : 'SHOW SAFE ROUTE'}</span>
          </button>

          <button
            onClick={() => onLayerModeChange(layerMode === 'risk' ? 'terrain' : 'risk')}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-heading font-bold bg-surface/95 backdrop-blur-md text-primary border border-border hover:bg-hover transition-all shadow-sm"
          >
            <Layers className="w-3.5 h-3.5 text-muted" />
            <span>{layerMode === 'risk' ? 'LAYERS: RISK' : 'LAYERS: TERRAIN'}</span>
          </button>
        </div>

        {/* Risk Forecast Timeline Bar */}
        <div className="bg-surface/90 backdrop-blur-md px-4 py-2 rounded-xl border border-border/50 flex items-center justify-between max-w-xl mx-auto text-xs font-mono shadow-sm">
          <span className="text-muted font-heading font-bold uppercase text-[10px]">RISK FORECAST:</span>
          <div className="flex items-center space-x-4">
            <span>NOW: <strong className="text-accent">LOW</strong></span>
            <span>+3h: <strong className="text-[#D88A32]">WATCH</strong></span>
            <span>+6h: <strong className="text-[#C6533C]">HIGH</strong></span>
            <span>+12h: <strong className="text-[#C6533C]">HIGH</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
