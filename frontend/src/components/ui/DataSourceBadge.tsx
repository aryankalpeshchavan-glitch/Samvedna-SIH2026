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
      className: 'bg-[#23483A]/10 text-[#23483A] border-[#23483A]/30',
    },
    synthetic: {
      label: 'STATIC REFERENCE',
      icon: Database,
      className: 'bg-[#536A72]/15 text-[#536A72] border-[#536A72]/40',
    },
    replayed: {
      label: 'REPLAYED FEED',
      icon: RotateCcw,
      className: 'bg-[#536A72]/15 text-[#536A72] border-[#536A72]/40',
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
