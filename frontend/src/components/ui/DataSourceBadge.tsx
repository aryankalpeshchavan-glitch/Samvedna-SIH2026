import React from 'react';
import { DataSourceType } from '../../types/emergency';
import { Radio, Database, RotateCcw } from 'lucide-react';

interface DataSourceBadgeProps {
  type: DataSourceType;
  size?: 'sm' | 'md';
}

export const DataSourceBadge: React.FC<DataSourceBadgeProps> = ({ type, size = 'sm' }) => {
  const config = {
    live: {
      label: 'LIVE GIS',
      icon: Radio,
      className: 'bg-accent/10 text-accent border-accent/30',
    },
    synthetic: {
      label: 'SYNTHETIC DEMO',
      icon: Database,
      className: 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/40',
    },
    replayed: {
      label: 'REPLAYED FEED',
      icon: RotateCcw,
      className: 'bg-muted/15 text-muted border-muted/40',
    },
  };

  const current = config[type] || config.synthetic;
  const Icon = current.icon;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold tracking-wider uppercase border rounded-md ${padding} ${current.className}`}
      title={`Data origin: ${current.label}`}
    >
      <Icon className="w-3 h-3 mr-1 shrink-0" />
      {current.label}
    </span>
  );
};
