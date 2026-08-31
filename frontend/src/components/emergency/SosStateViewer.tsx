import React from 'react';
import { SosState, SosStatusDetail } from '../../types/emergency';
import { DataSourceBadge } from '../ui/DataSourceBadge';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { useTranslation } from '../../i18n/LanguageContext';
import { Loader2, CheckCircle, Clock, ShieldAlert, PhoneCall, MapPin, UserCheck, CheckCheck } from 'lucide-react';

interface SosStateViewerProps {
  statusDetail: SosStatusDetail;
  onReset: () => void;
}

export const SosStateViewer: React.FC<SosStateViewerProps> = ({ statusDetail, onReset }) => {
  const { t } = useTranslation();

  const getStateConfig = (state: SosState) => {
    switch (state) {
      case 'SENDING':
        return {
          title: t('status.stateSending'),
          desc: t('status.stateSending'),
          icon: <Loader2 className="w-8 h-8 text-[#8E2F2B] animate-spin" />,
          color: 'border-[#8E2F2B] bg-[#8E2F2B]/10',
        };
      case 'OFFLINE_QUEUED':
        return {
          title: t('status.stateOfflineQueued'),
          desc: statusDetail.errorMessage || t('network.pending'),
          icon: <Clock className="w-8 h-8 text-[#D88A32]" />,
          color: 'border-[#D88A32] bg-[#D88A32]/10',
        };
      case 'SENT':
        return {
          title: t('status.stateSent'),
          desc: t('status.stateSent'),
          icon: <CheckCircle className="w-8 h-8 text-[#23483A]" />,
          color: 'border-[#23483A] bg-[#23483A]/10',
        };
      case 'VERIFIED':
        return {
          title: t('status.stateVerified'),
          desc: t('status.stateVerified'),
          icon: <ShieldAlert className="w-8 h-8 text-[#23483A]" />,
          color: 'border-[#23483A] bg-[#23483A]/10',
        };
      case 'ASSIGNED':
      case 'VOLUNTEER_EN_ROUTE':
        return {
          title: t('status.stateEnRoute'),
          desc: t('status.stateEnRoute'),
          icon: <UserCheck className="w-8 h-8 text-[#23483A]" />,
          color: 'border-[#23483A] bg-[#23483A]/15',
        };
      case 'HELP_ARRIVED':
      case 'RESOLVED':
        return {
          title: t('status.stateVerified'),
          desc: t('status.stateVerified'),
          icon: <CheckCheck className="w-8 h-8 text-[#23483A]" />,
          color: 'border-[#23483A] bg-[#23483A]/10',
        };
      case 'ERROR':
      default:
        return {
          title: t('status.stateSending'),
          desc: statusDetail.errorMessage || t('status.stateSending'),
          icon: <ShieldAlert className="w-8 h-8 text-[#8E2F2B]" />,
          color: 'border-[#8E2F2B] bg-[#8E2F2B]/15',
        };
    }
  };

  const config = getStateConfig(statusDetail.state);

  return (
    <Card className={`border-2 ${config.color} p-5 my-2 font-sans`}>
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-[#E8E6DC]">
        <span className="font-mono text-xs font-bold text-[#536A72] uppercase tracking-widest">
          SOS TRACKER &bull; {statusDetail.sosId || 'PENDING'}
        </span>
        <DataSourceBadge type="synthetic" />
      </div>

      <div className="flex items-start space-x-3.5">
        <div className="shrink-0 p-2 rounded-xl bg-[#FAF9F3] border border-[#C7B89B]/40">
          {config.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-base font-heading font-bold text-[#202622] tracking-wide uppercase">
            {config.title}
          </h3>
          <p className="mt-1 text-xs text-[#202622]/85 font-medium leading-relaxed">
            {config.desc}
          </p>

          {statusDetail.assignedVolunteerName && (
            <div className="mt-3 p-3 rounded-xl bg-[#FAF9F3] border border-[#23483A]/40 space-y-1">
              <div className="flex items-center text-[#23483A] font-heading font-bold text-xs">
                <UserCheck className="w-4 h-4 mr-1.5" />
                <span>{t('status.assignedResponder')} {statusDetail.assignedVolunteerName}</span>
              </div>
              {statusDetail.etaMinutes && (
                <div className="flex items-center text-xs text-[#536A72] font-mono">
                  <MapPin className="w-3.5 h-3.5 mr-1" />
                  <span>{t('status.eta')} <strong className="text-[#202622]">{statusDetail.etaMinutes} mins</strong></span>
                </div>
              )}
              {statusDetail.assignedVolunteerPhone && (
                <a
                  href={`tel:${statusDetail.assignedVolunteerPhone}`}
                  className="inline-flex items-center text-xs font-bold text-[#23483A] hover:underline pt-1"
                >
                  <PhoneCall className="w-3.5 h-3.5 mr-1" />
                  {t('status.callResponder')} ({statusDetail.assignedVolunteerPhone})
                </a>
              )}
            </div>
          )}

          {statusDetail.lastUpdatedText && (
            <p className="mt-2 text-[11px] font-mono text-[#536A72]">
              Latest Event: {statusDetail.lastUpdatedText}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-[#E8E6DC] flex items-center justify-between">
        <p className="text-xs text-[#536A72] font-mono">
          State: <span className="text-[#202622] font-bold">{statusDetail.state}</span>
        </p>
        <Button variant="outline" size="sm" onClick={onReset}>
          {t('status.resetButton')}
        </Button>
      </div>
    </Card>
  );
};
