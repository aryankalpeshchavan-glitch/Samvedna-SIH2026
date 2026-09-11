import React from 'react';
import { MOCK_SAFE_ROUTE } from '../../data/mockStoryData';
import { X, Navigation, ShieldCheck, AlertOctagon, MapPin } from 'lucide-react';
import { ModalPortal } from '../ui/ModalPortal';

interface SafeRouteOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SafeRouteOverlay: React.FC<SafeRouteOverlayProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <ModalPortal onClose={onClose}>
      <div
        role="region"
        aria-label="Safe Evacuation Route Guidance"
        className="fixed bottom-20 left-4 right-4 sm:left-auto sm:right-6 sm:max-w-md z-40 bg-[#FAF9F3]/95 backdrop-blur-md border-2 border-[#23483A] rounded-3xl p-5 shadow-2xl space-y-4 font-sans"
      >
      <div className="flex items-start justify-between pb-2 border-b border-[#E8E6DC]">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-[#23483A] text-[#FAF9F3]">
            <Navigation className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5 mb-0.5">
              <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-[#D88A32]/20 text-[#965C22] border border-[#D88A32]/40">
                SCENARIO / NOT A LIVE ROUTE
              </span>
            </div>
            <h3 className="text-base font-heading font-bold text-[#202622]">
              {MOCK_SAFE_ROUTE.title}
            </h3>
          </div>
        </div>
        <button onClick={onClose} className="text-[#536A72] hover:text-[#202622] p-1">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
          <span className="text-[#536A72] text-[10px] block">DISTANCE</span>
          <strong className="text-[#202622] text-sm">{MOCK_SAFE_ROUTE.distanceKm} km</strong>
        </div>
        <div className="p-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
          <span className="text-[#536A72] text-[10px] block">ESTIMATED TIME</span>
          <strong className="text-[#23483A] text-sm">{MOCK_SAFE_ROUTE.estMinutes} mins walk</strong>
        </div>
      </div>

      <div className="p-3 rounded-2xl bg-[#23483A]/10 border border-[#23483A]/30 space-y-1">
        <div className="flex items-center justify-between text-xs font-heading font-bold text-[#23483A]">
          <span className="flex items-center">
            <MapPin className="w-3.5 h-3.5 mr-1" /> {MOCK_SAFE_ROUTE.shelterName}
          </span>
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="text-[11px] font-mono text-[#536A72] flex justify-between">
          <span>Capacity: {MOCK_SAFE_ROUTE.shelterCapacity} persons</span>
          <span>Occupancy: {MOCK_SAFE_ROUTE.shelterOccupancyPct}%</span>
        </div>
      </div>

      <div className="text-xs font-mono text-[#C6533C] flex items-center space-x-1.5 pt-1">
        <AlertOctagon className="w-4 h-4 shrink-0" />
        <span>Avoid: {MOCK_SAFE_ROUTE.blockedRoads.join(', ')}</span>
      </div>
      </div>
    </ModalPortal>
  );
};
