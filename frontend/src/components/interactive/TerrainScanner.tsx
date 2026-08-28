import React, { useEffect, useRef, useState } from 'react';
import { MOCK_TERRAIN_SCAN } from '../../data/mockStoryData';
import { animateScannerLine } from '../../animations/storyAnimations';
import { X, Sparkles, Mountain, CloudRain, Droplets, Gauge, AlertTriangle } from 'lucide-react';

interface TerrainScannerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const TerrainScanner: React.FC<TerrainScannerProps> = ({ isOpen, onClose }) => {
  const lineRef = useRef<HTMLDivElement>(null);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setScanned(false);
      const anim = animateScannerLine(lineRef.current);
      const timer = setTimeout(() => {
        setScanned(true);
      }, 2500);

      return () => {
        anim?.pause();
        clearTimeout(timer);
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm">
      <div className="relative w-full max-w-lg bg-surface border-2 border-border rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 overflow-hidden">
        
        {/* Animated Scanner Bar Line */}
        {!scanned && (
          <div
            ref={lineRef}
            className="absolute left-0 right-0 h-1 bg-accent shadow-[0_0_15px_#00FA9A] z-10 pointer-events-none"
          />
        )}

        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-hover">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-border/10 text-border border border-border/30">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <span className="text-xs font-mono font-bold text-border uppercase tracking-widest block">
                ENVIRONMENTAL TOPOGRAPHY SCAN
              </span>
              <h2 className="text-xl font-heading font-bold text-primary">
                {scanned ? 'Scan Complete' : 'Scanning Local Terrain...'}
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-muted hover:text-primary hover:bg-hover"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scanning Animation / Telemetry Results */}
        {!scanned ? (
          <div className="py-12 text-center space-y-3 font-mono">
            <div className="w-12 h-12 rounded-full border-4 border-accent border-t-transparent animate-spin mx-auto" />
            <p className="text-xs text-muted">Extracting elevation contours, slope gradient & soil saturation...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-2xl bg-main border border-border/50">
                <Mountain className="w-4 h-4 text-border mb-1" />
                <span className="text-muted text-[10px] block">ELEVATION</span>
                <strong className="text-primary text-sm">{MOCK_TERRAIN_SCAN.elevationMeters} m</strong>
              </div>
              <div className="p-3 rounded-2xl bg-main border border-border/50">
                <Gauge className="w-4 h-4 text-[#C6533C] mb-1" />
                <span className="text-muted text-[10px] block">SLOPE ANGLE</span>
                <strong className="text-[#C6533C] text-sm">{MOCK_TERRAIN_SCAN.slopeDegrees}°</strong>
              </div>
              <div className="p-3 rounded-2xl bg-main border border-border/50">
                <CloudRain className="w-4 h-4 text-muted mb-1" />
                <span className="text-muted text-[10px] block">PRECIPITATION</span>
                <strong className="text-primary text-sm">{MOCK_TERRAIN_SCAN.rainfall24hMm} mm</strong>
              </div>
              <div className="p-3 rounded-2xl bg-main border border-border/50">
                <Droplets className="w-4 h-4 text-[#D88A32] mb-1" />
                <span className="text-muted text-[10px] block">SOIL SATURATION</span>
                <strong className="text-[#D88A32] text-sm">{MOCK_TERRAIN_SCAN.soilMoisturePct}%</strong>
              </div>
            </div>

            {/* Calculated Risk Index Card */}
            <div className="p-4 rounded-2xl bg-accent text-surface flex items-center justify-between shadow-md">
              <div>
                <span className="text-xs font-mono text-surface/80 uppercase block">COMPUTED RISK INDEX</span>
                <h3 className="text-xl font-heading font-bold mt-0.5">
                  {MOCK_TERRAIN_SCAN.riskCategory} STABILITY
                </h3>
              </div>
              <div className="text-right">
                <span className="text-3xl font-heading font-black text-surface font-mono">
                  {MOCK_TERRAIN_SCAN.riskScore}
                </span>
                <span className="text-xs font-mono text-surface/70 block">/ 100</span>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#D88A32]/10 border border-[#D88A32]/30 text-xs text-primary flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-[#D88A32] shrink-0 mt-0.5" />
              <span>{MOCK_TERRAIN_SCAN.recommendation}</span>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
