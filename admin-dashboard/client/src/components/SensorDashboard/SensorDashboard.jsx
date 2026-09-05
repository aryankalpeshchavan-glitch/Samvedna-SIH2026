import React, { useState, useEffect } from 'react';
import useStore from '../../store/useStore';
import { formatEta, getUnitIcon } from '../../utils/formatters';

export default function SensorDashboard() {
  const sensors = useStore((s) => s.sensors);
  const units = useStore((s) => s.units);
  const alerts = useStore((s) => s.alerts);
  const [tick, setTick] = useState(0);

  // Tick every second for countdown
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const hasLandslideAlert = sensors.some((s) => s.alert) || alerts.length > 0;
  const enRouteUnits = units.filter((u) => u.status === 'EN ROUTE');
  const onSiteUnits = units.filter((u) => u.status === 'ON SITE');

  // Find closest ETA
  const closestEta = enRouteUnits.length > 0
    ? Math.min(...enRouteUnits.map((u) => Math.max(0, (u.eta || 0) - (tick % 60))))
    : null;

  return (
    <div className={`sensor-dashboard ${hasLandslideAlert ? 'alert-active' : ''}`}>
      {/* Section 1: Sensor Readings */}
      <div className="sensor-readings-section">
        <div className="dashboard-section-title">📡 LIVE SENSOR READINGS</div>
        <div className="sensor-readings-grid">
          {sensors.length === 0 && (
            <div className="sensor-no-data">Waiting for sensor data…</div>
          )}
          {sensors.map((sensor) => (
            <div
              key={sensor.id}
              className={`sensor-reading-card ${sensor.alert ? 'sensor-alert' : ''}`}
            >
              <div className="sensor-reading-name">
                {sensor.alert && <span className="sensor-alert-dot" />}
                {sensor.name}
              </div>
              <div className="sensor-reading-values">
                <div className="sensor-value">
                  <span className="sensor-value-label">🌧 Rainfall</span>
                  <span className={`sensor-value-num ${sensor.rainfall > 50 ? 'danger' : sensor.rainfall > 30 ? 'warning' : ''}`}>
                    {sensor.rainfall} <small>mm/hr</small>
                  </span>
                </div>
                <div className="sensor-value">
                  <span className="sensor-value-label">💧 Moisture</span>
                  <span className={`sensor-value-num ${sensor.soilMoisture > 80 ? 'danger' : sensor.soilMoisture > 60 ? 'warning' : ''}`}>
                    {sensor.soilMoisture}<small>%</small>
                  </span>
                </div>
                <div className="sensor-value">
                  <span className="sensor-value-label">📐 Tilt</span>
                  <span className={`sensor-value-num ${sensor.tilt > 5 ? 'danger' : sensor.tilt > 3 ? 'warning' : ''}`}>
                    {sensor.tilt}<small>°</small>
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Alert Button */}
      <div className="alert-button-section">
        <button
          className={`alert-mega-btn ${hasLandslideAlert ? 'alert-triggered' : ''}`}
          disabled={!hasLandslideAlert}
        >
          <span className="alert-btn-icon">⚠</span>
          <span className="alert-btn-text">
            {hasLandslideAlert ? 'LANDSLIDE ALERT' : 'NO ALERT'}
          </span>
          {hasLandslideAlert && (
            <span className="alert-btn-sub">
              {sensors.filter((s) => s.alert).length} sensor(s) triggered
            </span>
          )}
        </button>
      </div>

      {/* Section 3: Rescue ETA & Route */}
      <div className="rescue-eta-section">
        <div className="dashboard-section-title">🚨 RESCUE RESPONSE</div>
        {enRouteUnits.length === 0 && onSiteUnits.length === 0 && (
          <div className="rescue-status-msg">No rescue units dispatched yet</div>
        )}
        {enRouteUnits.map((unit) => {
          const eta = Math.max(0, (unit.eta || 0) - (tick % 60));
          const progress = unit.route
            ? Math.min(100, Math.round(((unit.currentRouteIndex || 0) / (unit.route.length - 1)) * 100))
            : 0;
          return (
            <div key={unit.id} className="rescue-unit-card">
              <div className="rescue-unit-header">
                <span className="rescue-unit-icon">{getUnitIcon(unit.type)}</span>
                <span className="rescue-unit-id">{unit.id}</span>
                <span className="rescue-unit-type">{unit.type}</span>
                <span className="rescue-route-badge">🔵 EN ROUTE</span>
              </div>
              <div className="rescue-unit-details">
                <div className="rescue-eta">
                  <span className="rescue-eta-label">ETA</span>
                  <span className="rescue-eta-value">{formatEta(eta)}</span>
                </div>
                <div className="rescue-progress">
                  <div className="rescue-progress-bar">
                    <div className="rescue-progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                  <span className="rescue-progress-pct">{progress}%</span>
                </div>
                <div className="rescue-route-info">
                  Route shown in <span style={{ color: '#3b82f6', fontWeight: 700 }}>blue</span> on map
                </div>
              </div>
            </div>
          );
        })}
        {onSiteUnits.map((unit) => (
          <div key={unit.id} className="rescue-unit-card on-site">
            <div className="rescue-unit-header">
              <span className="rescue-unit-icon">{getUnitIcon(unit.type)}</span>
              <span className="rescue-unit-id">{unit.id}</span>
              <span className="rescue-unit-type">{unit.type}</span>
              <span className="rescue-onsite-badge">✅ ON SITE</span>
            </div>
          </div>
        ))}
        {closestEta !== null && (
          <div className="rescue-eta-summary">
            Nearest rescue arrives in <strong>{formatEta(closestEta)}</strong>
          </div>
        )}
      </div>
    </div>
  );
}
