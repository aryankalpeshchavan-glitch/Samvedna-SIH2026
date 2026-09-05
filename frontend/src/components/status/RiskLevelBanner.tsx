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
      border: 'border-[#23483A]/30 bg-[#23483A]/10',
      icon: Info,
      iconColor: 'text-[#23483A]',
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
    <div className={`p-4 rounded-2xl border ${current.border} bg-[#FAF9F3] my-2 transition-all font-sans`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2">
          <Icon className={`w-5 h-5 ${current.iconColor}`} />
          <span className="text-xs font-mono font-bold text-[#536A72] uppercase tracking-wide">
            REGIONAL HAZARD STATUS
          </span>
        </div>
        <Badge level={level} />
      </div>

      <p className="text-xs font-mono text-[#536A72] mb-1">
        Zone: <strong className="text-[#202622]">{regionName}</strong>
      </p>
      
      <p className="text-xs sm:text-sm font-medium text-[#202622] leading-relaxed">
        {current.desc}
      </p>
    </div>
  );
};
