import React from 'react';
import useStore from '../store/useStore';

export default function Toast() {
  const toasts = useStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className="toast">
          {t.message}
        </div>
      ))}
    </div>
  );
}
