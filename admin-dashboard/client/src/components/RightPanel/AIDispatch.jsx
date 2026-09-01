import React from 'react';
import useStore from '../../store/useStore';

const recommendations = [
  { qty: 2, type: 'Rescue Teams', icon: '🚒', reasoning: 'Steep terrain requires specialized rope & pulley rescue capability' },
  { qty: 1, type: 'Medical Unit (AMB-07)', icon: '🚑', reasoning: '7 persons in impact zone — triage and first aid required' },
  { qty: 1, type: 'Helicopter (AIR-01)', icon: '🚁', reasoning: 'Road access blocked by debris in zone B — aerial evacuation needed' },
  { qty: 1, type: 'Engineering Unit', icon: '🔧', reasoning: 'Road clearance needed for ground vehicle access' }
];

export default function AIDispatch({ socketRef }) {
  const addToast = useStore((s) => s.addToast);
  const units = useStore((s) => s.units);
  const enRouteCount = units.filter((u) => u.status === 'EN ROUTE').length;

  const handleDispatchAll = () => {
    if (socketRef?.current) {
      socketRef.current.emit('dispatch:all');
      addToast('🚀 All standby units dispatched to impact zone');
    }
  };

  return (
    <>
      <div className="panel-section-header">
        <span>🤖 AI Dispatch</span>
        <span className="count">Recommended</span>
      </div>
      <div className="panel-section-body">
        <div className="dispatch-card">
          {recommendations.map((rec, i) => (
            <div key={i}>
              <div className="dispatch-item">
                <span>{rec.icon}</span>
                <span style={{ fontWeight: 600 }}>{rec.qty}×</span>
                <span>{rec.type}</span>
              </div>
              <div className="dispatch-reasoning">{rec.reasoning}</div>
            </div>
          ))}

          <div style={{ padding: '8px 0 4px', fontSize: 12, color: 'var(--text-secondary)' }}>
            Est. full response arrival: <strong style={{ color: 'var(--text-primary)' }}>22 min</strong>
          </div>

          <div className="dispatch-footer">
            <button
              className="btn btn-primary btn-sm"
              style={{ flex: 1 }}
              onClick={handleDispatchAll}
              id="dispatch-all-btn"
            >
              ✓ DISPATCH ALL
            </button>
            <button className="btn btn-sm" style={{ flex: 0.6 }} id="dispatch-edit-btn">
              EDIT
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
