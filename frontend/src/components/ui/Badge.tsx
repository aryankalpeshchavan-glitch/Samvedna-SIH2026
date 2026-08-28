import React from 'react';
import { SeverityLevel } from '../../types/emergency';

interface BadgeProps {
  level: SeverityLevel;
}

export const Badge: React.FC<BadgeProps> = ({ level }) => {
  const styles = {
    LOW: 'bg-[#23483A]/10 text-[#23483A] border-[#23483A]/30',
    WATCH: 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/40',
    MEDIUM: 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/40',
    HIGH: 'bg-[#C6533C]/15 text-[#C6533C] border-[#C6533C]/40',
    CRITICAL: 'bg-[#8E2F2B]/15 text-[#8E2F2B] border-[#8E2F2B]/50 font-black',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-heading font-bold uppercase tracking-wider border ${styles[level]}`}
      role="status"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5" />
      {level}
    </span>
  );
};
