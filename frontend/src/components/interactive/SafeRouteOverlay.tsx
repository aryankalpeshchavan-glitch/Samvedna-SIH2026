import React from 'react';
import { MOCK_SAFE_ROUTE } from '../../data/mockStoryData';
import { X, Navigation, ShieldCheck, AlertOctagon, MapPin } from 'lucide-react';

interface SafeRouteOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SafeRouteOverlay: React.FC<SafeRouteOverlayProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed bottom-20 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md z-40 bg-surface/95 backdrop-blur-md border-2 border-accent rounded-3xl p-5 shadow-2xl space-y-4 font-sans">
      <div className="flex items-start justify-between pb-2 border-b border-hover">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-accent text-surface">
            <Navigation className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold text-accent uppercase tracking-widest block">
              SAFE EVACUATION CORRIDOR
            </span>
            <h3 className="text-base font-heading font-bold text-primary">
              {MOCK_SAFE_ROUTE.title}
            </h3>
          </div>
        </div>
        <button onClick={onClose} className="text-muted hover:text-primary p-1">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded-xl bg-main border border-border/40">
          <span className="text-muted text-[10px] block">DISTANCE</span>
          <strong className="text-primary text-sm">{MOCK_SAFE_ROUTE.distanceKm} km</strong>
        </div>
        <div className="p-2.5 rounded-xl bg-main border border-border/40">
          <span className="text-muted text-[10px] block">ESTIMATED TIME</span>
          <strong className="text-accent text-sm">{MOCK_SAFE_ROUTE.estMinutes} mins walk</strong>
        </div>
      </div>

      <div className="p-3 rounded-2xl bg-accent/10 border border-accent/30 space-y-1">
        <div className="flex items-center justify-between text-xs font-heading font-bold text-accent">
          <span className="flex items-center">
            <MapPin className="w-3.5 h-3.5 mr-1" /> {MOCK_SAFE_ROUTE.shelterName}
          </span>
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="text-[11px] font-mono text-muted flex justify-between">
          <span>Capacity: {MOCK_SAFE_ROUTE.shelterCapacity} persons</span>
          <span>Occupancy: {MOCK_SAFE_ROUTE.shelterOccupancyPct}%</span>
        </div>
      </div>

      <div className="text-xs font-mono text-[#C6533C] flex items-center space-x-1.5 pt-1">
        <AlertOctagon className="w-4 h-4 shrink-0" />
        <span>Avoid: {MOCK_SAFE_ROUTE.blockedRoads.join(', ')}</span>
      </div>
    </div>
  );
};
