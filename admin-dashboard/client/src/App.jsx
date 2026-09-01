import React from 'react';
import useSocket from './hooks/useSocket';
import useStore from './store/useStore';
import TopBar from './components/TopBar';
import LeftPanel from './components/LeftPanel/LeftPanel';
import RightPanel from './components/RightPanel/RightPanel';
import CesiumMap from './components/CesiumMap/CesiumMap';
import SensorDashboard from './components/SensorDashboard/SensorDashboard';
import Toast from './components/Toast';

export default function App() {
  const socketRef = useSocket();
  const leftCollapsed = useStore((s) => s.leftCollapsed);
  const rightCollapsed = useStore((s) => s.rightCollapsed);
  const toggleLeft = useStore((s) => s.toggleLeft);
  const toggleRight = useStore((s) => s.toggleRight);
  const sensors = useStore((s) => s.sensors);
  const alerts = useStore((s) => s.alerts);

  const hasLandslideAlert = sensors.some((s) => s.alert) || alerts.length > 0;

  return (
    <div className={`app-layout ${hasLandslideAlert ? 'landslide-alert-active' : ''}`}>
      <TopBar />

      {/* Flickering red side lights when alert is active */}
      {hasLandslideAlert && (
        <>
          <div className="alert-side-light left-light" />
          <div className="alert-side-light right-light" />
        </>
      )}

      <div className="app-main">
        <LeftPanel collapsed={leftCollapsed} />

        <button
          className={`panel-toggle left ${leftCollapsed ? 'collapsed' : ''}`}
          onClick={toggleLeft}
          title={leftCollapsed ? 'Show panel' : 'Hide panel'}
        >
          {leftCollapsed ? '›' : '‹'}
        </button>

        <div className="center-column">
          <CesiumMap socketRef={socketRef} />
          <SensorDashboard />
        </div>

        <button
          className={`panel-toggle right ${rightCollapsed ? 'collapsed' : ''}`}
          onClick={toggleRight}
          title={rightCollapsed ? 'Show panel' : 'Hide panel'}
        >
          {rightCollapsed ? '‹' : '›'}
        </button>

        <RightPanel collapsed={rightCollapsed} socketRef={socketRef} />
      </div>
      <Toast />
    </div>
  );
}
