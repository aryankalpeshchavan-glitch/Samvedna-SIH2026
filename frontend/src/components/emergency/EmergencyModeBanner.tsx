import React from 'react';
import { ShieldAlert, Navigation, X, MapPin } from 'lucide-react';
import { MOCK_SAFE_ROUTE } from '../../data/mockStoryData';
import { useTranslation } from '../../i18n/LanguageContext';
import { AudioAlertButton } from '../ui/AudioAlertButton';

interface EmergencyModeBannerProps {
  onShowRoute: () => void;
  onExitEmergencyMode: () => void;
}

export const EmergencyModeBanner: React.FC<EmergencyModeBannerProps> = ({
  onShowRoute,
  onExitEmergencyMode,
}) => {
  const { t } = useTranslation();

  return (
    <div className="w-full bg-[#8E2F2B] text-[#FAF9F3] p-4 sm:p-5 rounded-2xl border-2 border-[#8E2F2B] shadow-xl space-y-3 font-sans">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2.5">
          <ShieldAlert className="w-6 h-6 text-[#FAF9F3] shrink-0 animate-pulse" />
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-[#FAF9F3]/80 uppercase block">
              {t('evac.title')}
            </span>
            <h3 className="text-lg font-heading font-black tracking-wide uppercase">
              {t('evac.title')}
            </h3>
          </div>
        </div>
        <button
          onClick={onExitEmergencyMode}
          className="text-[#FAF9F3]/70 hover:text-white p-1 rounded-full hover:bg-black/20"
          title="Exit Emergency Mode"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <p className="text-xs sm:text-sm text-[#FAF9F3]/90 font-medium leading-relaxed">
        {t('evac.subtitle')}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono pt-1">
        <div className="p-2.5 rounded-xl bg-black/20 border border-white/10 flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-[#D88A32] shrink-0" />
          <span>AVOID: <strong>{MOCK_SAFE_ROUTE.blockedRoads[0]}</strong></span>
        </div>
        <div className="p-2.5 rounded-xl bg-black/20 border border-white/10 flex items-center space-x-2">
          <Navigation className="w-4 h-4 text-[#FAF9F3] shrink-0" />
          <span>SHELTER: <strong>{MOCK_SAFE_ROUTE.shelterName}</strong></span>
        </div>
      </div>

      <div className="pt-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={onShowRoute}
            className="px-5 py-2.5 rounded-xl bg-[#FAF9F3] text-[#8E2F2B] font-heading font-bold text-xs hover:bg-[#E8E6DC] transition-colors flex items-center space-x-2 shadow-sm cursor-pointer"
          >
            <Navigation className="w-4 h-4" />
            <span>{t('evac.viewRoute')}</span>
          </button>

          <AudioAlertButton text={`${t('evac.title')}. ${t('evac.subtitle')}`} size="sm" />
        </div>

        <span className="text-[11px] font-mono text-[#FAF9F3]/70">
          Source: Regional Disaster Authority
        </span>
      </div>
    </div>
  );
};
