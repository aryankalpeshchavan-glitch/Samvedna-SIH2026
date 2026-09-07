import React, { useState, useRef, useEffect } from 'react';
import { IncidentCategory, SeverityLevel } from '../types/emergency';
import { Button } from '../components/ui/Button';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { animatePageEnter } from '../animations/pageTransitions';
import { useTranslation } from '../i18n/LanguageContext';
import { Camera, Send, CheckCircle2, Mountain, Waves, UserX, Stethoscope, Building2, AlertCircle, MapPin } from 'lucide-react';

import { SpecularHeading } from '../components/ui/SpecularHeading';

import { savePendingAction } from '../services/offlineStorage';
import { getNetworkStatus } from '../services/network';
import { IncidentReportPayload } from '../types/emergency';

interface IncidentReportProps {
  onSubmit: (category: IncidentCategory, severity: SeverityLevel, note: string) => void;
}

const REPORT_OPTIONS: { id: IncidentCategory; icon: React.ElementType }[] = [
  { id: 'LANDSLIDE', icon: Mountain },
  { id: 'SLOPE_CRACK', icon: AlertCircle },
  { id: 'ROAD_BLOCKED', icon: Building2 },
  { id: 'FLOOD', icon: Waves },
  { id: 'BUILDING_DAMAGE', icon: Building2 },
  { id: 'PERSON_TRAPPED', icon: UserX },
  { id: 'OTHER', icon: Stethoscope },
];

export const IncidentReport: React.FC<IncidentReportProps> = ({ onSubmit }) => {
  const { t } = useTranslation();
  const [selectedCat, setSelectedCat] = useState<IncidentCategory>('LANDSLIDE');
  const [severity, setSeverity] = useState<SeverityLevel>('WATCH');
  const [note, setNote] = useState('');
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [isOfflineSaved, setIsOfflineSaved] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const url = URL.createObjectURL(file);
      setPhotoPreview(url);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const network = getNetworkStatus();
    if (network === 'OFFLINE') {
      const payload: IncidentReportPayload = {
        id: `REP-${Date.now().toString(36).toUpperCase()}`,
        category: selectedCat,
        severity,
        description: note,
        location: {
          latitude: 26.14,
          longitude: 91.73,
          status: 'LOCATION_DETECTED',
          addressName: 'Guwahati Sector 4',
        },
        timestamp: Date.now(),
      };
      await savePendingAction('INCIDENT_REPORT', payload);
      setIsOfflineSaved(true);
    } else {
      setIsOfflineSaved(false);
    }
    onSubmit(selectedCat, severity, note);
    setSubmitted(true);
  };

  const selectedCatTranslated = t(`hazards.${selectedCat}`);

  if (submitted) {
    return (
      <div className="pb-24 pt-8 px-4 max-w-xl mx-auto text-center space-y-4 font-sans">
        <div className={`w-16 h-16 rounded-full border-2 flex items-center justify-center mx-auto ${
          isOfflineSaved ? 'bg-[#D88A32]/10 border-[#D88A32] text-[#D88A32]' : 'bg-[#23483A]/10 border-[#23483A] text-[#23483A]'
        }`}>
          <CheckCircle2 className="w-10 h-10" />
        </div>
        <h2 className="text-2xl font-heading font-black text-[#202622]">
          {isOfflineSaved ? t('report.offlineSuccessTitle') : t('report.successTitle')}
        </h2>
        <p className="text-sm text-[#202622]/80 leading-relaxed font-medium">
          {isOfflineSaved
            ? t('report.offlineSuccessMessage', { category: selectedCatTranslated })
            : t('report.successMessage', { category: selectedCatTranslated })}
        </p>
        <div className="pt-4">
          <Button variant="secondary" onClick={() => setSubmitted(false)}>
            {t('report.anotherButton')}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-6 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#C7B89B]/50">
        <div>
          <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest block">
            {t('report.subtitle')}
          </span>
          <h2 className="text-xl font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
            {t('report.title')}
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* 1. Category Selection Grid */}
        <div>
          <label className="block text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider mb-2">
            {t('report.step1')}
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {REPORT_OPTIONS.map((item) => {
              const Icon = item.icon;
              const isSelected = selectedCat === item.id;
              const label = t(`hazards.${item.id}`);
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedCat(item.id)}
                  className={`p-3 rounded-2xl border text-left flex flex-col justify-between transition-all tactile-press cursor-pointer ${
                    isSelected
                      ? 'bg-[#23483A] text-[#FAF9F3] border-[#23483A] shadow-md'
                      : 'bg-[#FAF9F3] text-[#202622] border-[#C7B89B]/50 hover:bg-[#E8E6DC]'
                  }`}
                >
                  <Icon className={`w-5 h-5 mb-2 ${isSelected ? 'text-[#FAF9F3]' : 'text-[#23483A]'}`} />
                  <span className="text-xs font-heading font-bold">{label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Photo Upload */}
        <div>
          <label className="block text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider mb-2">
            {t('report.step2')}
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handlePhotoUpload}
            className="hidden"
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            className="p-4 rounded-2xl border-2 border-dashed border-[#C7B89B] bg-[#FAF9F3] hover:bg-[#E8E6DC] cursor-pointer flex flex-col items-center justify-center text-center transition-colors"
          >
            {photoPreview ? (
              <div className="relative w-full h-32 rounded-xl overflow-hidden">
                <img src={photoPreview} alt="Upload Preview" className="w-full h-full object-cover" />
                <span className="absolute bottom-2 right-2 px-2 py-1 bg-[#202622]/80 text-white text-[10px] rounded font-mono">
                  {t('report.photoAttached')}
                </span>
              </div>
            ) : (
              <>
                <Camera className="w-6 h-6 text-[#23483A] mb-1" />
                <span className="text-xs font-heading font-bold text-[#202622]">{t('report.uploadPhoto')}</span>
                <span className="text-[10px] text-[#536A72] font-mono mt-0.5">{t('report.uploadLimit')}</span>
              </>
            )}
          </div>
        </div>

        {/* 3. Location Auto Detection */}
        <div className="p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/50 text-xs font-mono text-[#536A72] flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-[#23483A]" />
            <span>{t('report.gpsLabel')} <strong className="text-[#202622]">{t('report.gpsAuto')}</strong></span>
          </div>
          <span className="text-[#23483A] font-bold">26.14° N, 91.73° E (Demo GPS)</span>
        </div>

        {/* 4. Severity Toggles */}
        <div>
          <label className="block text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider mb-2">
            {t('report.step4')}
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'LOW' },
              { id: 'WATCH' },
              { id: 'CRITICAL' },
            ].map((lvl) => {
              const label = t(`severity.${lvl.id}`);
              return (
                <button
                  key={lvl.id}
                  type="button"
                  onClick={() => setSeverity(lvl.id as SeverityLevel)}
                  className={`py-2.5 text-xs font-heading font-bold rounded-xl border transition-colors cursor-pointer ${
                    severity === lvl.id
                      ? 'bg-[#23483A] text-[#FAF9F3] border-[#23483A]'
                      : 'bg-[#FAF9F3] text-[#202622] border-[#C7B89B]/50 hover:bg-[#E8E6DC]'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 5. Optional Note */}
        <div>
          <label className="block text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider mb-2">
            {t('report.step5')}
          </label>
          <textarea
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={t('report.notePlaceholder')}
            className="w-full p-3 rounded-xl bg-[#FAF9F3] border border-[#C7B89B] text-sm text-[#202622] placeholder-[#536A72]/60 focus:border-[#23483A] focus:outline-none"
          />
        </div>

        <Button variant="secondary" size="lg" fullWidth type="submit">
          <Send className="w-4 h-4 mr-2" />
          {t('report.submitButton')}
        </Button>
      </form>
    </div>
  );
};
