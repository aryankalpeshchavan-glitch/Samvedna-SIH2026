import React from 'react';
import { NetworkStatusType } from '../../types/emergency';
import { Wifi, WifiOff, Activity } from 'lucide-react';

interface NetworkIndicatorProps {
  status: NetworkStatusType;
}

export const NetworkIndicator: React.FC<NetworkIndicatorProps> = ({ status }) => {
  const config = {
    ONLINE: {
      label: 'ONLINE',
      icon: Wifi,
      className: 'bg-accent/10 text-accent border-accent/30',
      dot: 'bg-accent',
    },
    WEAK: {
      label: 'WEAK SIGNAL',
      icon: Activity,
      className: 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/40',
      dot: 'bg-[#D88A32]',
    },
    OFFLINE: {
      label: 'OFFLINE (LOCAL)',
      icon: WifiOff,
      className: 'bg-[#8E2F2B]/15 text-[#8E2F2B] border-[#8E2F2B]/40',
      dot: 'bg-[#8E2F2B]',
    },
  };

  const current = config[status] || config.OFFLINE;
  const Icon = current.icon;

  return (
    <div
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-bold border transition-colors ${current.className}`}
      role="status"
      aria-label={`Network status: ${current.label}`}
    >
      <span className={`w-2 h-2 rounded-full ${current.dot} mr-1.5 animate-pulse`} />
      <Icon className="w-3.5 h-3.5 mr-1" />
      <span>{current.label}</span>
    </div>
  );
};
