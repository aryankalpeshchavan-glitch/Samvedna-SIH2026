import React, { useRef, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { AudioAlertButton } from '../components/ui/AudioAlertButton';
import { animatePageEnter } from '../animations/pageTransitions';
import { useTranslation } from '../i18n/LanguageContext';
import { LifeBuoy, PhoneCall, ShieldAlert, AlertTriangle, Waves, Activity, Building2, MessageSquare, Phone } from 'lucide-react';

export const CustomerServiceHelp: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { t } = useTranslation();

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  // Dynamically computed localized speech synthesis readout text
  const helplineAudioText = `${t('help.ndrfTitle')}: 1078. ${t('help.seocTitle')}: 1070. ${t('help.medicalTitle')}: 108. ${t('help.policeTitle')}: 112. ${t('help.fireTitle')}: 101. ${t('help.tollFreeSub')}`;

  const helplines = [
    {
      title: t('help.ndrfTitle'),
      number: '1078',
      altNumber: '+91 11 26701728',
      desc: t('help.ndrfDesc'),
      icon: ShieldAlert,
      color: 'border-[#8E2F2B] text-[#8E2F2B] bg-[#8E2F2B]/10',
      badge: 'NATIONAL 24/7',
    },
    {
      title: t('help.seocTitle'),
      number: '1070',
      altNumber: '+91 361 2237221',
      desc: t('help.seocDesc'),
      icon: LifeBuoy,
      color: 'border-[#23483A] text-[#23483A] bg-[#23483A]/10',
      badge: 'STATE SEOC',
    },
    {
      title: t('help.medicalTitle'),
      number: '108',
      altNumber: '102',
      desc: t('help.medicalDesc'),
      icon: PhoneCall,
      color: 'border-[#8E2F2B] text-[#8E2F2B] bg-[#8E2F2B]/10',
      badge: 'AMBULANCE',
    },
    {
      title: t('help.policeTitle'),
      number: '112',
      altNumber: '100',
      desc: t('help.policeDesc'),
      icon: Phone,
      color: 'border-[#23483A] text-[#23483A] bg-[#23483A]/10',
      badge: 'POLICE ERSS',
    },
    {
      title: t('help.fireTitle'),
      number: '101',
      altNumber: '+91 361 2540101',
      desc: t('help.fireDesc'),
      icon: AlertTriangle,
      color: 'border-[#D88A32] text-[#D88A32] bg-[#D88A32]/10',
      badge: 'RESCUE',
    },
  ];

  return (
    <div ref={containerRef} className="pb-28 pt-4 px-4 max-w-2xl mx-auto space-y-6 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#C7B89B]/50">
        <div>
          <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest block">
            {t('help.categoryHeader')}
          </span>
          <h2 className="text-xl font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
            {t('help.title')}
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      {/* Subtitle & Audio Readout Banner */}
      <div className="p-4 rounded-2xl bg-[#FAF9F3] border-2 border-[#23483A]/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-3 rounded-2xl bg-[#23483A] text-[#FAF9F3] shrink-0">
            <LifeBuoy className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-heading font-bold text-[#202622]">
              {t('help.subtitle')}
            </h3>
            <span className="text-xs font-mono text-[#536A72]">
              {t('help.tollFreeSub')}
            </span>
          </div>
        </div>
        <AudioAlertButton text={helplineAudioText} size="sm" />
      </div>

      {/* 1. Toll-Free Emergency Helplines Section */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest flex items-center">
          <PhoneCall className="w-4 h-4 mr-1.5" />
          {t('help.helplinesHeader')}
        </h3>

        <div className="grid grid-cols-1 gap-3">
          {helplines.map((item, idx) => (
            <Card key={idx} className="p-4 bg-[#FAF9F3] border-[#C7B89B] shadow-sm hover:border-[#23483A] transition-colors">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-start space-x-3">
                  <div className={`p-2.5 rounded-xl border ${item.color} shrink-0 mt-0.5`}>
                    <item.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-heading font-bold text-[#202622]">
                        {item.title}
                      </h4>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#202622]/10 text-[#202622]">
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-xs text-[#536A72] mt-0.5 leading-relaxed font-medium">
                      {item.desc}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  <a
                    href={`tel:${item.number}`}
                    className="px-4 py-2 rounded-xl bg-[#8E2F2B] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#722421] transition-colors flex items-center space-x-1.5 shadow-sm cursor-pointer"
                  >
                    <PhoneCall className="w-3.5 h-3.5" />
                    <span>{t('help.callNow')} ({item.number})</span>
                  </a>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* 2. Official Disaster Response Directory */}
      <Card className="p-5 bg-[#F4F1E8] border-[#C7B89B] space-y-3">
        <h3 className="text-xs font-mono font-bold text-[#202622] uppercase tracking-widest flex items-center">
          <Building2 className="w-4 h-4 mr-1.5 text-[#23483A]" />
          {t('help.agenciesHeader')}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
          <div className="p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/50 space-y-1">
            <strong className="text-[#202622] block font-bold">{t('help.ndrfHq')}</strong>
            <span className="text-[#536A72] text-[11px] block">{t('help.ndrfLoc')}</span>
            <a href="tel:+913612840001" className="text-[#23483A] font-bold hover:underline block pt-1">
              +91 361 2840001
            </a>
          </div>

          <div className="p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/50 space-y-1">
            <strong className="text-[#202622] block font-bold">{t('help.sdrfHq')}</strong>
            <span className="text-[#536A72] text-[11px] block">{t('help.sdrfLoc')}</span>
            <a href="tel:+913612237011" className="text-[#23483A] font-bold hover:underline block pt-1">
              +91 361 2237011
            </a>
          </div>

          <div className="p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/50 space-y-1">
            <strong className="text-[#202622] block font-bold">{t('help.mdonerHq')}</strong>
            <span className="text-[#536A72] text-[11px] block">{t('help.mdonerLoc')}</span>
            <a href="tel:+913642522000" className="text-[#23483A] font-bold hover:underline block pt-1">
              +91 364 2522000
            </a>
          </div>
        </div>
      </Card>

      {/* 3. Emergency Survival Guidance Checklists */}
      <div className="space-y-3">
        <h3 className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest flex items-center">
          <Activity className="w-4 h-4 mr-1.5" />
          {t('help.guidanceHeader')}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Card className="p-3.5 bg-[#FAF9F3] border-[#C7B89B] space-y-2">
            <div className="flex items-center space-x-2 text-[#8E2F2B]">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <h4 className="text-xs font-heading font-bold uppercase">{t('help.landslideTitle')}</h4>
            </div>
            <p className="text-xs text-[#202622]/90 leading-relaxed font-medium">
              {t('help.landslideGuidance')}
            </p>
          </Card>

          <Card className="p-3.5 bg-[#FAF9F3] border-[#C7B89B] space-y-2">
            <div className="flex items-center space-x-2 text-[#23483A]">
              <Waves className="w-4 h-4 shrink-0" />
              <h4 className="text-xs font-heading font-bold uppercase">{t('help.floodTitle')}</h4>
            </div>
            <p className="text-xs text-[#202622]/90 leading-relaxed font-medium">
              {t('help.floodGuidance')}
            </p>
          </Card>

          <Card className="p-3.5 bg-[#FAF9F3] border-[#C7B89B] space-y-2">
            <div className="flex items-center space-x-2 text-[#D88A32]">
              <Activity className="w-4 h-4 shrink-0" />
              <h4 className="text-xs font-heading font-bold uppercase">{t('help.quakeTitle')}</h4>
            </div>
            <p className="text-xs text-[#202622]/90 leading-relaxed font-medium">
              {t('help.quakeGuidance')}
            </p>
          </Card>
        </div>
      </div>

      {/* 4. Offline SMS Emergency Shortcode Notice */}
      <Card className="p-4 bg-[#8E2F2B]/10 border-2 border-[#8E2F2B]/40 space-y-2">
        <div className="flex items-center space-x-2 text-[#8E2F2B]">
          <MessageSquare className="w-5 h-5 shrink-0" />
          <h4 className="text-xs font-heading font-black uppercase tracking-wider">
            {t('help.offlineTitle')}
          </h4>
        </div>
        <p className="text-xs text-[#202622] font-mono leading-relaxed">
          {t('help.offlineMessage')}
        </p>
      </Card>

    </div>
  );
};
