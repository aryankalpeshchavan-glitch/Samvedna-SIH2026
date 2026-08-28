import React, { useEffect, useState, useRef } from 'react';
import { SosState, SosStatusDetail } from '../types/emergency';
import { PendingSosEntry } from '../types/storage';
import { getPendingSOS } from '../services/offlineStorage';
import { SosStateViewer } from '../components/emergency/SosStateViewer';
import { Card } from '../components/ui/Card';
import { animatePageEnter } from '../animations/pageTransitions';
import { Activity, Database, RefreshCw, Layers } from 'lucide-react';

interface StatusProps {
  sosState: SosState;
  statusDetail: SosStatusDetail;
  onResetSos: () => void;
  onSimulateStateChange: (newState: SosState) => void;
}

export const Status: React.FC<StatusProps> = ({
  sosState,
  statusDetail,
  onResetSos,
  onSimulateStateChange,
}) => {
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
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-4 font-sans">
      <div className="flex items-center justify-between pb-2 border-b border-border/50">
        <div>
          <span className="text-xs font-mono font-bold text-accent uppercase tracking-widest block">
            DISPATCH LAYER
          </span>
          <h2 className="text-lg font-heading font-black text-primary uppercase tracking-wide">
            SOS Status & Buffer
          </h2>
        </div>
        <button
          onClick={fetchOfflineList}
          className="p-2 rounded-xl bg-surface border border-border text-primary hover:bg-hover"
          title="Refresh IndexedDB entries"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Active SOS Tracker */}
      {sosState !== 'IDLE' ? (
        <SosStateViewer statusDetail={statusDetail} onReset={onResetSos} />
      ) : (
        <Card className="text-center p-8 border-dashed border-border">
          <Activity className="w-10 h-10 text-muted mx-auto mb-2 opacity-60" />
          <h3 className="text-base font-heading font-bold text-primary">No Active Emergency Signal</h3>
          <p className="text-xs text-muted mt-1 max-w-xs mx-auto">
            You currently have no active SOS request in progress. Use the SOS control on the Map screen when emergency help is required.
          </p>
        </Card>
      )}

      {/* Interactive State Simulation Controls */}
      <Card className="p-4 bg-surface border-border">
        <h4 className="text-xs font-mono font-bold text-accent uppercase mb-2 flex items-center">
          <Layers className="w-4 h-4 mr-1.5" /> State Machine Simulator (Demo)
        </h4>
        <p className="text-xs text-muted mb-3">
          Simulate full backend dispatch lifecycle transitions:
        </p>
        <div className="flex flex-wrap gap-2">
          {(['IDLE', 'SENDING', 'SENT', 'OFFLINE_QUEUED', 'VERIFIED', 'VOLUNTEER_EN_ROUTE', 'RESOLVED', 'ERROR'] as SosState[]).map((state) => (
            <button
              key={state}
              onClick={() => onSimulateStateChange(state)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-semibold border transition-colors ${
                sosState === state
                  ? 'bg-accent text-surface border-accent font-bold'
                  : 'bg-main text-primary border-border/50 hover:bg-hover'
              }`}
            >
              {state}
            </button>
          ))}
        </div>
      </Card>

      {/* IndexedDB Local Persistence Queue */}
      <div className="pt-2">
        <h3 className="text-xs font-mono font-bold text-muted uppercase tracking-widest mb-3 flex items-center">
          <Database className="w-4 h-4 mr-1.5 text-accent" />
          IndexedDB Local Pending Queue ({offlineSosList.length})
        </h3>

        {offlineSosList.length === 0 ? (
          <p className="text-xs text-muted font-mono italic">
            No pending offline payloads stored in browser IndexedDB.
          </p>
        ) : (
          <div className="space-y-2">
            {offlineSosList.map((entry) => (
              <Card key={entry.id} className="p-3 text-xs font-mono border-border">
                <div className="flex items-center justify-between text-primary">
                  <span className="font-bold text-accent">{entry.id}</span>
                  <span className="text-muted">{new Date(entry.createdAt).toLocaleTimeString()}</span>
                </div>
                <div className="mt-1 text-muted text-[11px] flex justify-between">
                  <span>Network on trigger: <strong>{entry.payload.networkStatusOnTrigger}</strong></span>
                  <span>Synced: <strong>{entry.synced ? 'YES' : 'NO (QUEUED)'}</strong></span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
