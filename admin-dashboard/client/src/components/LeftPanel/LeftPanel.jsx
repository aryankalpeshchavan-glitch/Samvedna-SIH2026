import React from 'react';
import ActiveAlerts from './ActiveAlerts';
import PeopleAtRisk from './PeopleAtRisk';

export default function LeftPanel({ collapsed }) {
  return (
    <aside className={`panel left ${collapsed ? 'collapsed' : ''}`} id="left-panel">
      <div style={{ display: collapsed ? 'none' : 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="panel-section" style={{ height: '40%', borderBottom: '1px solid var(--border-subtle)' }}>
          <ActiveAlerts />
        </div>
        <div className="panel-section" style={{ flex: 1 }}>
          <PeopleAtRisk />
        </div>
      </div>
    </aside>
  );
}
