import React from 'react';
import { SosState, SosStatusDetail } from '../../types/emergency';
import { DataSourceBadge } from '../ui/DataSourceBadge';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Loader2, CheckCircle, Clock, ShieldAlert, PhoneCall, MapPin, UserCheck, CheckCheck } from 'lucide-react';

interface SosStateViewerProps {
  statusDetail: SosStatusDetail;
  onReset: () => void;
}

export const SosStateViewer: React.FC<SosStateViewerProps> = ({ statusDetail, onReset }) => {
  const getStateConfig = (state: SosState) => {
    switch (state) {
      case 'SENDING':
        return {
          title: 'TRANSMITTING SOS SIGNAL...',
          desc: 'Connecting to CrisisCore regional relay network.',
          icon: <Loader2 className="w-8 h-8 text-[#8E2F2B] animate-spin" />,
          color: 'border-[#8E2F2B] bg-[#8E2F2B]/10',
        };
      case 'OFFLINE_QUEUED':
        return {
          title: 'SAVED LOCALLY (OFFLINE QUEUE)',
          desc: statusDetail.errorMessage || 'No active connection. SOS payload saved in IndexedDB and queued to auto-sync upon reconnection.',
          icon: <Clock className="w-8 h-8 text-[#D88A32]" />,
          color: 'border-[#D88A32] bg-[#D88A32]/10',
        };
      case 'SENT':
        return {
          title: 'SOS TRANSMITTED SUCCESSFULLY',
          desc: 'Received by regional dispatch node. Verification in progress.',
          icon: <CheckCircle className="w-8 h-8 text-accent" />,
          color: 'border-accent bg-accent/10',
        };
      case 'VERIFIED':
        return {
          title: 'SOS VERIFIED BY OPERATOR',
          desc: 'Disaster coordination center has confirmed your location.',
          icon: <ShieldAlert className="w-8 h-8 text-accent" />,
          color: 'border-accent bg-accent/10',
        };
      case 'ASSIGNED':
      case 'VOLUNTEER_EN_ROUTE':
        return {
          title: 'RESCUE VOLUNTEER DISPATCHED',
          desc: `Assigned NDRF certified volunteer is moving toward your location.`,
          icon: <UserCheck className="w-8 h-8 text-accent" />,
          color: 'border-accent bg-accent/15',
        };
      case 'HELP_ARRIVED':
      case 'RESOLVED':
        return {
          title: 'RESCUE COMPLETED / RESOLVED',
          desc: 'Emergency responder has reached location or incident closed.',
          icon: <CheckCheck className="w-8 h-8 text-accent" />,
          color: 'border-accent bg-accent/10',
        };
      case 'ERROR':
      default:
        return {
          title: 'TRANSMISSION ERROR',
          desc: statusDetail.errorMessage || 'Failed to dispatch SOS. Please try calling local emergency services directly.',
          icon: <ShieldAlert className="w-8 h-8 text-[#8E2F2B]" />,
          color: 'border-[#8E2F2B] bg-[#8E2F2B]/15',
        };
    }
  };

  const config = getStateConfig(statusDetail.state);

  return (
    <Card className={`border-2 ${config.color} p-5 my-2 font-sans`}>
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-hover">
        <span className="font-mono text-xs font-bold text-muted uppercase tracking-widest">
          SOS TRACKER &bull; {statusDetail.sosId || 'PENDING'}
        </span>
        <DataSourceBadge type="synthetic" />
      </div>

      <div className="flex items-start space-x-3.5">
        <div className="shrink-0 p-2 rounded-xl bg-surface border border-border/40">
          {config.icon}
        </div>
        <div className="flex-1">
          <h3 className="text-base font-heading font-bold text-primary tracking-wide uppercase">
            {config.title}
          </h3>
          <p className="mt-1 text-xs text-primary/85 font-medium leading-relaxed">
            {config.desc}
          </p>

          {statusDetail.assignedVolunteerName && (
            <div className="mt-3 p-3 rounded-xl bg-surface border border-accent/40 space-y-1">
              <div className="flex items-center text-accent font-heading font-bold text-xs">
                <UserCheck className="w-4 h-4 mr-1.5" />
                <span>{statusDetail.assignedVolunteerName}</span>
              </div>
              {statusDetail.etaMinutes && (
                <div className="flex items-center text-xs text-muted font-mono">
                  <MapPin className="w-3.5 h-3.5 mr-1" />
                  <span>Arrival ETA: <strong className="text-primary">{statusDetail.etaMinutes} mins</strong></span>
                </div>
              )}
              {statusDetail.assignedVolunteerPhone && (
                <a
                  href={`tel:${statusDetail.assignedVolunteerPhone}`}
                  className="inline-flex items-center text-xs font-bold text-accent hover:underline pt-1"
                >
                  <PhoneCall className="w-3.5 h-3.5 mr-1" />
                  Call Responder ({statusDetail.assignedVolunteerPhone})
                </a>
              )}
            </div>
          )}

          {statusDetail.lastUpdatedText && (
            <p className="mt-2 text-[11px] font-mono text-muted">
              Latest Event: {statusDetail.lastUpdatedText}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-hover flex items-center justify-between">
        <p className="text-xs text-muted font-mono">
          State: <span className="text-primary font-bold">{statusDetail.state}</span>
        </p>
        <Button variant="outline" size="sm" onClick={onReset}>
          Reset SOS
        </Button>
      </div>
    </Card>
  );
};
