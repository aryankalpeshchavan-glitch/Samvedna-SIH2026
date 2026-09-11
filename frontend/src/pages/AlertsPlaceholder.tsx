import React, { useRef, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { Badge } from '../components/ui/Badge';
import { animatePageEnter } from '../animations/pageTransitions';
import { useTranslation } from '../i18n/LanguageContext';
import { AudioAlertButton } from '../components/ui/AudioAlertButton';
import { Bell, ShieldAlert } from 'lucide-react';

export const AlertsPlaceholder: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const alert1Title = t('evac.title');
  const alert1Body = t('evac.subtitle');

  const alert2Title = t('hazards.FLASH_FLOOD');
  const alert2Body = t('report.offlineSuccessMessage', { category: t('hazards.FLASH_FLOOD') });

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-4 font-sans">
      <div className="flex items-center justify-between pb-2 border-b border-[#C7B89B]/50">
        <div>
          <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest block">
            {t('alerts.headerTag')}
          </span>
          <h2 className="text-xl font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
            {t('alerts.title')}
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/50 text-xs font-mono">
        <div className="flex items-center space-x-2 text-[#202622]">
          <ShieldAlert className="w-4 h-4 text-[#23483A]" />
          <span>{t('alerts.sub')}</span>
        </div>
      </div>

      <div className="space-y-4">
        {/* Critical Evacuation Warning Notice */}
        <Card className="p-5 border-2 border-[#8E2F2B] bg-[#FAF9F3] space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-heading font-bold text-[#8E2F2B] uppercase tracking-wider flex items-center">
              <Bell className="w-4 h-4 mr-1.5" /> {t('alerts.officialWarning')}
            </span>
            <Badge level="CRITICAL" />
          </div>

          <h3 className="text-base font-heading font-bold text-[#202622]">
            {alert1Title}
          </h3>

          <p className="text-xs text-[#202622]/90 leading-relaxed font-medium">
            {alert1Body}
          </p>

          <div className="pt-2 flex items-center justify-between border-t border-[#E8E6DC] text-[11px] font-mono text-[#536A72]">
            <span>Issued: 14 mins ago &bull; Regional Disaster Authority</span>
            <AudioAlertButton text={`${alert1Title}. ${alert1Body}`} size="sm" />
          </div>
        </Card>

        {/* High Flash Flood Advisory Notice */}
        <Card className="p-5 border border-[#D88A32] bg-[#FAF9F3] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-heading font-bold text-[#D88A32] uppercase tracking-wider flex items-center">
              <Bell className="w-4 h-4 mr-1.5" /> {alert2Title}
            </span>
            <Badge level="HIGH" />
          </div>

          <h3 className="text-base font-heading font-bold text-[#202622]">
            {alert2Title} Advisory
          </h3>

          <p className="text-xs text-[#202622]/90 leading-relaxed font-medium">
            {alert2Body}
          </p>

          <div className="pt-2 flex items-center justify-between border-t border-[#E8E6DC] text-[11px] font-mono text-[#536A72]">
            <span>Issued: 45 mins ago &bull; Hydro-Sensor Mesh</span>
            <AudioAlertButton text={`${alert2Title}. ${alert2Body}`} size="sm" />
          </div>
        </Card>
      </div>
    </div>
  );
};
