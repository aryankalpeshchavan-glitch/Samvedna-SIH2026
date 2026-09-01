import React from 'react';
import AIDispatch from './AIDispatch';
import UnitsInField from './UnitsInField';

export default function RightPanel({ collapsed, socketRef }) {
  return (
    <aside className={`panel right ${collapsed ? 'collapsed' : ''}`} id="right-panel">
      <div style={{ display: collapsed ? 'none' : 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="panel-section" style={{ height: '38%', borderBottom: '1px solid var(--border-subtle)' }}>
          <AIDispatch socketRef={socketRef} />
        </div>
        <div className="panel-section" style={{ flex: 1 }}>
          <UnitsInField />
        </div>
      </div>
    </aside>
  );
}
