import React, { useState } from 'react';
import { NetworkStatusType } from '../../types/emergency';
import { useOfflineSync } from '../../hooks/useOfflineSync';
import { Wifi, WifiOff, Activity, RefreshCw, HardDrive, CheckCircle, AlertTriangle, X } from 'lucide-react';

interface NetworkIndicatorProps {
  status: NetworkStatusType;
}

export const NetworkIndicator: React.FC<NetworkIndicatorProps> = ({ status }) => {
  const { syncState, pendingCount, pendingItems, triggerSync } = useOfflineSync();
  const [showModal, setShowModal] = useState(false);

  const config = {
    ONLINE: {
      label: 'ONLINE',
      message: 'Connected',
      icon: Wifi,
      className: 'bg-[#23483A]/10 text-[#23483A] border-[#23483A]/30',
      dot: 'bg-[#23483A]',
    },
    WEAK: {
      label: 'WEAK SIGNAL',
      message: 'Weak Signal — queued sync active',
      icon: Activity,
      className: 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/40',
      dot: 'bg-[#D88A32]',
    },
    OFFLINE: {
      label: 'OFFLINE MODE',
      message: 'Offline mode — your emergency request will be saved on this device.',
      icon: WifiOff,
      className: 'bg-[#8E2F2B]/15 text-[#8E2F2B] border-[#8E2F2B]/40',
      dot: 'bg-[#8E2F2B]',
    },
  };

  const current = config[status] || config.OFFLINE;
  const Icon = current.icon;

  return (
    <>
      <div
        role="status"
        aria-label={`Network status: ${current.label}`}
        className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-mono font-bold border transition-all space-x-1.5 ${current.className}`}
      >
        <span className={`w-2 h-2 rounded-full ${current.dot} animate-pulse`} />
        <Icon className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">{current.label}</span>
        {pendingCount > 0 && (
          <span className="px-1.5 py-0.5 rounded-full bg-[#8E2F2B] text-[#FAF9F3] text-[10px] font-black animate-bounce">
            {pendingCount}
          </span>
        )}
      </div>

      {/* Offline Sync Status & Hackathon Demo Drawer */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/60 backdrop-blur-sm animate-fade-in font-sans">
          <div className="bg-[#FAF9F3] border-2 border-[#C7B89B] rounded-3xl max-w-lg w-full p-6 shadow-2xl relative space-y-5">
            
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-3 border-b border-[#C7B89B]/50">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-2xl bg-[#23483A]/10 text-[#23483A] border border-[#23483A]/30">
                  <HardDrive className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-heading font-black text-[#202622] uppercase tracking-wide">
                    Offline & IndexedDB Status
                  </h3>
                  <span className="text-xs font-mono text-[#536A72] block">
                    Frontend Local Storage Engine
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-xl hover:bg-[#E8E6DC] text-[#202622]/60 hover:text-[#202622]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Network Status Card */}
            <div className={`p-4 rounded-2xl border ${current.className} flex items-center justify-between`}>
              <div className="flex items-center space-x-3">
                <Icon className="w-6 h-6" />
                <div>
                  <span className="text-xs font-mono font-bold uppercase tracking-wider block">
                    Connection State: {current.label}
                  </span>
                  <p className="text-xs font-medium mt-0.5">
                    {current.message}
                  </p>
                </div>
              </div>
            </div>

            {/* Sync State Status Messages */}
            <div className="p-4 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/50 space-y-2 text-xs font-sans">
              <div className="flex items-center justify-between font-mono font-bold text-[#536A72] uppercase tracking-wider">
                <span>Sync Engine Status:</span>
                <span className={`px-2 py-0.5 rounded text-[10px] ${
                  syncState === 'SYNCING'
                    ? 'bg-[#D88A32] text-white animate-pulse'
                    : syncState === 'SYNCED'
                    ? 'bg-[#23483A] text-white'
                    : 'bg-[#C7B89B]/40 text-[#202622]'
                }`}>
                  {syncState}
                </span>
              </div>

              {syncState === 'SYNCING' && (
                <div className="flex items-center space-x-2 text-[#D88A32] font-bold">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Connection restored — sending saved requests...</span>
                </div>
              )}

              {syncState === 'SYNCED' && (
                <div className="flex items-center space-x-2 text-[#23483A] font-bold">
                  <CheckCircle className="w-4 h-4" />
                  <span>Emergency request successfully transmitted.</span>
                </div>
              )}

              {pendingCount > 0 && syncState === 'IDLE' && (
                <div className="flex items-center space-x-2 text-[#8E2F2B] font-bold">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Saved locally — waiting for connection ({pendingCount} pending).</span>
                </div>
              )}

              {pendingCount === 0 && syncState === 'IDLE' && (
                <p className="text-[#536A72]">
                  No pending requests in local storage. All emergency triggers are in sync.
                </p>
              )}
            </div>

            {/* IndexedDB Queue List */}
            {pendingItems.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider block">
                  Pending Local Queue ({pendingItems.length} stored items):
                </span>
                <div className="max-h-40 overflow-y-auto space-y-2 pr-1">
                  {pendingItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-3 rounded-xl bg-white border border-[#C7B89B]/50 flex items-center justify-between text-xs font-mono"
                    >
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="px-1.5 py-0.5 rounded bg-[#23483A] text-white font-black text-[10px]">
                            {item.type}
                          </span>
                          <span className="font-bold text-[#202622]">{item.id}</span>
                        </div>
                        <span className="text-[10px] text-[#536A72] block mt-1">
                          Created: {new Date(item.createdAt).toLocaleTimeString()}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.status === 'PENDING' ? 'bg-[#D88A32]/20 text-[#D88A32]' : 'bg-[#23483A]/20 text-[#23483A]'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions / Hackathon Controls */}
            <div className="pt-2 flex items-center space-x-3">
              <button
                onClick={() => triggerSync()}
                disabled={syncState === 'SYNCING' || pendingCount === 0}
                className="flex-1 py-2.5 px-4 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold flex items-center justify-center space-x-2 hover:bg-[#1b382d] disabled:opacity-50 transition-colors"
              >
                <RefreshCw className={`w-4 h-4 ${syncState === 'SYNCING' ? 'animate-spin' : ''}`} />
                <span>Transmit Pending Queue Now</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
