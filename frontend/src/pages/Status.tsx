import React, { useEffect, useState, useRef } from 'react';
import { SosState, SosStatusDetail } from '../types/emergency';
import { PendingSosEntry } from '../types/storage';
import { getPendingSOS } from '../services/offlineStorage';
import { SosStateViewer } from '../components/emergency/SosStateViewer';
import { Card } from '../components/ui/Card';
import { animatePageEnter } from '../animations/pageTransitions';
import { useTranslation } from '../i18n/LanguageContext';
import { SpecularHeading } from '../components/ui/SpecularHeading';
import { Activity, Database, RefreshCw, Layers, QrCode, ShieldCheck } from 'lucide-react';

interface StatusProps {
  sosState: SosState;
  statusDetail: SosStatusDetail;
  onResetSos: () => void;
  onSimulateStateChange: (newState: SosState) => void;
  onOpenQrScanner?: () => void;
}

export const Status: React.FC<StatusProps> = ({
  sosState,
  statusDetail,
  onResetSos,
  onSimulateStateChange,
  onOpenQrScanner,
}) => {
  const { t } = useTranslation();
  const [offlineSosList, setOfflineSosList] = useState<PendingSosEntry[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchOfflineList = async () => {
    const list = await getPendingSOS();
    setOfflineSosList(list);
  };

  useEffect(() => {
    animatePageEnter(containerRef.current);
    fetchOfflineList();
  }, []);

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-5 font-sans">
      
      {/* Page Header */}
      <div className="flex items-center justify-between pb-2 border-b border-[#C7B89B]/50">
        <div>
          <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-widest block">
            {t('status.headerTag')}
          </span>
          <h2 className="text-lg font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
            {t('status.headerTitle')}
          </h2>
        </div>
        <button
          onClick={fetchOfflineList}
          className="p-2 rounded-xl bg-[#FAF9F3] border border-[#C7B89B] text-[#202622] hover:bg-[#E8E6DC] cursor-pointer"
          title="Refresh IndexedDB entries"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Active SOS Tracker */}
      {sosState !== 'IDLE' ? (
        <SosStateViewer statusDetail={statusDetail} onReset={onResetSos} />
      ) : (
        <Card className="text-center p-8 border-dashed border-[#C7B89B]">
          <Activity className="w-10 h-10 text-[#536A72] mx-auto mb-2 opacity-60" />
          <h3 className="text-base font-heading font-bold text-[#202622]">{t('status.noSignalTitle')}</h3>
          <p className="text-xs text-[#536A72] mt-1 max-w-xs mx-auto">
            {t('status.noSignalText')}
          </p>
        </Card>
      )}

      {/* Dedicated Visually-Separated Volunteer Verification Feature Section (~32px vertical separation) */}
      {onOpenQrScanner && (
        <div className="mt-8 pt-6 border-t-2 border-dashed border-[#C7B89B]/60 space-y-3">
          <Card className="p-4 bg-[#FAF9F3] border-[#23483A]/30 flex items-center justify-between shadow-sm">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-2xl bg-[#23483A]/10 text-[#23483A]">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-heading font-bold text-[#202622]">
                  {t('qr.verifyTitle')}
                </h4>
                <p className="text-xs text-[#536A72]">
                  Scan NDRF / SDRF responder QR badge credentials.
                </p>
              </div>
            </div>
            <button
              onClick={onOpenQrScanner}
              className="px-4 py-2 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs flex items-center space-x-1.5 hover:bg-[#1b382d] transition-colors cursor-pointer shadow-sm shrink-0"
            >
              <QrCode className="w-4 h-4" />
              <span>{t('qr.startCamera')}</span>
            </button>
          </Card>
        </div>
      )}

      {/* Interactive State Simulation Controls */}
      <Card className="p-4 bg-[#FAF9F3] border-[#C7B89B]">
        <h4 className="text-xs font-mono font-bold text-[#23483A] uppercase mb-2 flex items-center">
          <Layers className="w-4 h-4 mr-1.5" /> {t('status.simulatorTitle')}
        </h4>
        <p className="text-xs text-[#536A72] mb-3">
          {t('status.simulatorText')}
        </p>
        <div className="flex flex-wrap gap-2">
          {(['IDLE', 'SENDING', 'SENT', 'OFFLINE_QUEUED', 'VERIFIED', 'VOLUNTEER_EN_ROUTE', 'RESOLVED', 'ERROR'] as SosState[]).map((state) => (
            <button
              key={state}
              onClick={() => onSimulateStateChange(state)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-semibold border transition-colors cursor-pointer ${
                sosState === state
                  ? 'bg-[#23483A] text-[#FAF9F3] border-[#23483A] font-bold'
                  : 'bg-[#F4F1E8] text-[#202622] border-[#C7B89B]/50 hover:bg-[#E8E6DC]'
              }`}
            >
              {state}
            </button>
          ))}
        </div>
      </Card>

      {/* IndexedDB Local Persistence Queue */}
      <div className="pt-2">
        <h3 className="text-xs font-mono font-bold text-[#536A72] uppercase tracking-widest mb-3 flex items-center">
          <Database className="w-4 h-4 mr-1.5 text-[#23483A]" />
          {t('status.queueTitle')} ({offlineSosList.length})
        </h3>

        {offlineSosList.length === 0 ? (
          <p className="text-xs text-[#536A72] font-mono italic">
            {t('status.queueEmpty')}
          </p>
        ) : (
          <div className="space-y-2">
            {offlineSosList.map((entry) => (
              <Card key={entry.id} className="p-3 text-xs font-mono border-[#C7B89B]">
                <div className="flex items-center justify-between text-[#202622]">
                  <span className="font-bold text-[#23483A]">{entry.id}</span>
                  <span className="text-[#536A72]">{new Date(entry.createdAt).toLocaleTimeString()}</span>
                </div>
                <div className="mt-1 text-[#536A72] text-[11px] flex justify-between">
                  <span>{t('status.networkOnTrigger')} <strong>{entry.payload.networkStatusOnTrigger}</strong></span>
                  <span>{t('status.synced')} <strong>{entry.synced ? t('status.yes') : t('status.noQueued')}</strong></span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
