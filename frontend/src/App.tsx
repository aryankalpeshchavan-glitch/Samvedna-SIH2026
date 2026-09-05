import { useState } from 'react';
import { useNetworkStatus } from './hooks/useNetworkStatus';
import { useLocationStatus } from './hooks/useLocationStatus';
import { useSosState } from './hooks/useSosState';
import { Header } from './components/navigation/Header';
import { BottomNav, TabType } from './components/navigation/BottomNav';
import { Home } from './pages/Home';
import { IncidentReport } from './pages/IncidentReport';
import { Status } from './pages/Status';
import { FamilyPlaceholder } from './pages/FamilyPlaceholder';
import { AlertsPlaceholder } from './pages/AlertsPlaceholder';
import { CustomerServiceHelp } from './pages/CustomerServiceHelp';
import { SosConfirmModal } from './components/emergency/SosConfirmModal';
import { VolunteerQrScannerModal } from './components/emergency/VolunteerQrScannerModal';
import { IncidentCategory, SeverityLevel, SosState } from './types/emergency';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [isQrScannerOpen, setIsQrScannerOpen] = useState(false);
  const networkStatus = useNetworkStatus();
  const { location, refreshLocation } = useLocationStatus();

  const {
    sosState,
    statusDetail,
    initiateSos,
    cancelSos,
    confirmAndTriggerSos,
    resetSos,
    setSosState,
  } = useSosState();

  const handleIncidentSubmit = (category: IncidentCategory, _severity: SeverityLevel, note: string) => {
    // Submit hazard report and automatically trigger emergency tracking
    confirmAndTriggerSos(category, note);
    setActiveTab('status');
  };

  const handleConfirmSosModal = (category?: IncidentCategory) => {
    confirmAndTriggerSos(category);
    setActiveTab('status');
  };

  return (
    <div className="min-h-screen bg-canvas text-gray-100 flex flex-col font-sans selection:bg-red-600 selection:text-white">
      {/* Top Header */}
      <Header
        networkStatus={networkStatus}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenQrScanner={() => setIsQrScannerOpen(true)}
        onOpenHelp={() => setActiveTab('help')}
      />

      {/* Main Content Area — Responsive Padding Prevents Dock Overlap on Desktop (lg:pl-24) & Mobile (pb-28) */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 lg:pl-24 py-4">
        {activeTab === 'home' && (
          <Home
            location={location}
            refreshLocation={refreshLocation}
            networkStatus={networkStatus}
            sosState={sosState}
            statusDetail={statusDetail}
            onTriggerSos={initiateSos}
            onResetSos={resetSos}
            onNavigate={setActiveTab}
          />
        )}

        {activeTab === 'incident' && (
          <IncidentReport onSubmit={handleIncidentSubmit} />
        )}

        {activeTab === 'status' && (
          <Status
            sosState={sosState}
            statusDetail={statusDetail}
            onResetSos={resetSos}
            onSimulateStateChange={(state: SosState) => {
              setSosState(state);
            }}
            onOpenQrScanner={() => setIsQrScannerOpen(true)}
          />
        )}

        {activeTab === 'family' && <FamilyPlaceholder />}

        {activeTab === 'alerts' && <AlertsPlaceholder />}

        {activeTab === 'help' && <CustomerServiceHelp />}
      </main>

      {/* Emergency Confirmation Modal */}
      {sosState === 'SOS_CONFIRMATION' && (
        <SosConfirmModal
          onConfirm={handleConfirmSosModal}
          onCancel={cancelSos}
        />
      )}

      {/* Volunteer QR Code Scanner Modal */}
      <VolunteerQrScannerModal
        isOpen={isQrScannerOpen}
        onClose={() => setIsQrScannerOpen(false)}
      />

      {/* Single Unified Floating Navigation Dock (Left Vertical on Desktop, Bottom Horizontal on Mobile) */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        sosState={sosState}
      />
    </div>
  );
}

export default App;
