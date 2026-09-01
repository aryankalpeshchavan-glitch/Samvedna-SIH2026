import React, { useState, useEffect } from 'react';
import useStore from '../../store/useStore';
import { formatEta, getStatusClass, getUnitIcon } from '../../utils/formatters';

export default function UnitsInField() {
  const units = useStore((s) => s.units);
  const selectUnit = useStore((s) => s.selectUnit);
  const [tick, setTick] = useState(0);

  // Tick every second for ETA countdown
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const getProgress = (unit) => {
    if (unit.status !== 'EN ROUTE' || !unit.route) return 0;
    const idx = unit.currentRouteIndex || 0;
    return Math.min(100, Math.round((idx / (unit.route.length - 1)) * 100));
  };

  return (
    <>
      <div className="panel-section-header">
        <span>Units in Field</span>
        <span className="count">{units.length} units</span>
      </div>
      <div className="panel-section-body">
        {units.map((unit) => (
          <div
            key={unit.id}
            className="unit-row"
            id={`unit-${unit.id}`}
            onClick={() => selectUnit(unit)}
          >
            <div className="unit-icon">{getUnitIcon(unit.type)}</div>
            <div className="unit-info">
              <div className="unit-id">{unit.id}</div>
              <div className="unit-detail">
                {unit.type} · {unit.driver}
              </div>
              {unit.status === 'EN ROUTE' && (
                <div className="progress-bar" style={{ marginTop: 4 }}>
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${getProgress(unit)}%` }}
                  />
                </div>
              )}
            </div>
            <div className="unit-meta">
              <span className={`status-chip ${getStatusClass(unit.status)}`}>
                {unit.status}
              </span>
              {unit.status === 'EN ROUTE' && unit.eta > 0 && (
                <span className="eta-label">
                  ETA {formatEta(Math.max(0, unit.eta - tick % 60))}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
