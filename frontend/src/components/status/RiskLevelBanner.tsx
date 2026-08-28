import React from 'react';
import { SeverityLevel } from '../../types/emergency';
import { Badge } from '../ui/Badge';
import { ShieldAlert, AlertTriangle, Info } from 'lucide-react';

interface RiskLevelBannerProps {
  level: SeverityLevel;
  regionName?: string;
}

export const RiskLevelBanner: React.FC<RiskLevelBannerProps> = ({
  level = 'HIGH',
  regionName = 'Northeast India Sector 4 (Assam / Meghalaya / Sikkim)',
}) => {
  const config = {
    LOW: {
      border: 'border-accent/30 bg-accent/10',
      icon: Info,
      iconColor: 'text-accent',
      desc: 'Normal seasonal weather pattern. No immediate landslide or surge threat detected.',
    },
    WATCH: {
      border: 'border-[#D88A32]/40 bg-[#D88A32]/10',
      icon: AlertTriangle,
      iconColor: 'text-[#D88A32]',
      desc: 'Precipitation threshold elevated. Soil saturation increasing across upper slope sectors.',
    },
    MEDIUM: {
      border: 'border-[#D88A32]/40 bg-[#D88A32]/10',
      icon: AlertTriangle,
      iconColor: 'text-[#D88A32]',
      desc: 'Moderate rain accumulation. Stay alert near steep slopes and river banks.',
    },
    HIGH: {
      border: 'border-[#C6533C]/40 bg-[#C6533C]/10',
      icon: AlertTriangle,
      iconColor: 'text-[#C6533C]',
      desc: 'Heavy monsoon rainfall. High risk of debris flow and flash flooding within 6 hours.',
    },
    CRITICAL: {
      border: 'border-[#8E2F2B] bg-[#8E2F2B]/15 shadow-md',
      icon: ShieldAlert,
      iconColor: 'text-[#8E2F2B]',
      desc: 'CRITICAL HAZARD WARNING: Imminent landslide risk. Relocate to high-ground community shelter immediately.',
    },
  };

  const current = config[level] || config.HIGH;
  const Icon = current.icon;

  return (
    <div className={`p-4 rounded-2xl border ${current.border} bg-surface my-2 transition-all font-sans`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2">
          <Icon className={`w-5 h-5 ${current.iconColor}`} />
          <span className="text-xs font-mono font-bold text-muted uppercase tracking-wide">
            REGIONAL HAZARD STATUS
          </span>
        </div>
        <Badge level={level} />
      </div>

      <p className="text-xs font-mono text-muted mb-1">
        Zone: <strong className="text-primary">{regionName}</strong>
      </p>
      
      <p className="text-xs sm:text-sm font-medium text-primary leading-relaxed">
        {current.desc}
      </p>
    </div>
  );
};
