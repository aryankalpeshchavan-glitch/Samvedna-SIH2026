import React from 'react';
import { LocationData } from '../../types/emergency';
import { MapPin, Navigation, AlertCircle, RefreshCw } from 'lucide-react';

interface LocationBarProps {
  location: LocationData;
  onRefresh: () => void;
}

export const LocationBar: React.FC<LocationBarProps> = ({ location, onRefresh }) => {
  const getStatusText = () => {
    switch (location.status) {
      case 'LOCATION_DETECTED':
        if (location.latitude && location.longitude) {
          return `${location.latitude.toFixed(4)}° N, ${location.longitude.toFixed(4)}° E (±${Math.round(location.accuracy || 15)}m)`;
        }
        return 'GPS Location Detected';
      case 'REQUESTING_LOCATION':
        return 'Acquiring GPS Satellite Signals...';
      case 'PERMISSION_DENIED':
        return 'GPS Permission Denied. Please enable location.';
      case 'LOCATION_UNAVAILABLE':
      default:
        return 'Location Services Unavailable';
    }
  };

  const getStatusColor = () => {
    switch (location.status) {
      case 'LOCATION_DETECTED':
        return 'text-[#23483A] bg-[#23483A]/10 border-[#23483A]/30';
      case 'REQUESTING_LOCATION':
        return 'text-[#D88A32] bg-[#D88A32]/10 border-[#D88A32]/30';
      case 'PERMISSION_DENIED':
      case 'LOCATION_UNAVAILABLE':
      default:
        return 'text-[#C6533C] bg-[#C6533C]/10 border-[#C6533C]/30';
    }
  };

  return (
    <div className={`flex items-center justify-between p-2.5 rounded-xl border text-xs font-mono font-medium ${getStatusColor()} bg-[#FAF9F3]`}>
      <div className="flex items-center space-x-2 min-w-0 pr-2">
        {location.status === 'LOCATION_DETECTED' ? (
          <MapPin className="w-4 h-4 shrink-0 text-[#23483A]" />
        ) : location.status === 'REQUESTING_LOCATION' ? (
          <Navigation className="w-4 h-4 shrink-0 text-[#D88A32] animate-spin" />
        ) : (
          <AlertCircle className="w-4 h-4 shrink-0 text-[#C6533C]" />
        )}
        <span className="truncate">{getStatusText()}</span>
      </div>

      <button
        onClick={onRefresh}
        className="shrink-0 p-1.5 rounded-lg hover:bg-[#E8E6DC] text-[#536A72] hover:text-[#202622] transition-colors"
        title="Refresh GPS Coordinates"
        aria-label="Refresh GPS location coordinates"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
