import React, { useState, useEffect } from 'react';
import useStore from '../store/useStore';
import { clockTime } from '../utils/formatters';

export default function TopBar() {
  const [time, setTime] = useState(clockTime());
  const connected = useStore((s) => s.connected);
  const sensors = useStore((s) => s.sensors);

  useEffect(() => {
    const interval = setInterval(() => setTime(clockTime()), 1000);
    return () => clearInterval(interval);
  }, []);

  const onlineCount = sensors.filter((s) => !s.alert || true).length;

  return (
    <header className="topbar" id="topbar">
      <div className="topbar-logo">
        <div className="topbar-logo-icon">▲</div>
        <span>LANDSLIDE AI</span>
      </div>

      <div className="topbar-center">
        <span className="topbar-clock">{time}</span>
        <span style={{ opacity: 0.6 }}>|</span>
        <span>Early Warning & Response System</span>
      </div>

      <div className="topbar-right">
        <span>
          <span className={`connection-dot ${connected ? 'connected' : 'disconnected'}`} />
          {connected ? 'LIVE' : 'OFFLINE'}
        </span>
        <span style={{ opacity: 0.4 }}>|</span>
        <span>Sensors Online: {onlineCount}/25</span>
      </div>
    </header>
  );
}
