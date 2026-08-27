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
import { SosConfirmModal } from './components/emergency/SosConfirmModal';
import { IncidentCategory, SeverityLevel, SosState } from './types/emergency';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('home');
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
      />

      {/* Main Content Area — Expands to Widescreen Workstation Layout on Desktop */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
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
          />
        )}

        {activeTab === 'family' && <FamilyPlaceholder />}

        {activeTab === 'alerts' && <AlertsPlaceholder />}
      </main>

      {/* Emergency Confirmation Modal */}
      {sosState === 'SOS_CONFIRMATION' && (
        <SosConfirmModal
          onConfirm={handleConfirmSosModal}
          onCancel={cancelSos}
        />
      )}

      {/* Bottom Navigation (Active on Mobile, Hidden on Desktop) */}
      <BottomNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        sosState={sosState}
      />
    </div>
  );
}

export default App;
