import React from 'react';
import useStore from '../../store/useStore';
import { timeAgo, getSeverityClass } from '../../utils/formatters';

export default function ActiveAlerts() {
  const alerts = useStore((s) => s.alerts);
  const selectAlert = useStore((s) => s.selectAlert);

  return (
    <>
      <div className="panel-section-header">
        <span>⚠ Active Alerts</span>
        <span className="count">{alerts.length}</span>
      </div>
      <div className="panel-section-body">
        {alerts.length === 0 && (
          <div style={{ padding: 16, color: 'var(--text-tertiary)', fontSize: 12, textAlign: 'center' }}>
            No active alerts
          </div>
        )}
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="card"
            id={`alert-${alert.id}`}
            onClick={() => selectAlert(alert)}
          >
            <div className="card-title">
              <span className={`badge ${getSeverityClass(alert.severity)}`}>
                {alert.severity}
              </span>
              <span>Landslide #{alert.id}</span>
            </div>
            <div className="card-detail">
              <div>📍 {alert.location}</div>
              <div>🌧 Trigger: {alert.trigger}</div>
            </div>
            <div className="card-meta">
              <span>Confidence: {alert.confidence}%</span>
              <span>{timeAgo(alert.timestamp)}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
