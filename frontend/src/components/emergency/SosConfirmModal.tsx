import React, { useRef, useEffect } from 'react';
import { animateModalEntrance } from '../../animations/sosAnimations';
import { Button } from '../ui/Button';
import { AlertOctagon, X, CheckCircle2 } from 'lucide-react';
import { IncidentCategory } from '../../types/emergency';

interface SosConfirmModalProps {
  onConfirm: (category?: IncidentCategory) => void;
  onCancel: () => void;
}

export const SosConfirmModal: React.FC<SosConfirmModalProps> = ({ onConfirm, onCancel }) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const [selectedCategory, setSelectedCategory] = React.useState<IncidentCategory | undefined>(undefined);

  useEffect(() => {
    animateModalEntrance(modalRef.current);
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/70 backdrop-blur-sm font-sans"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-md bg-surface border-2 border-[#8E2F2B] rounded-3xl p-6 shadow-2xl text-left space-y-4"
      >
        <div className="flex items-start justify-between pb-3 border-b border-hover">
          <div className="flex items-center space-x-2 text-[#8E2F2B]">
            <AlertOctagon className="w-6 h-6 shrink-0" />
            <h2 id="modal-title" className="text-xl font-heading font-black tracking-wide text-primary uppercase">
              Confirm Emergency SOS
            </h2>
          </div>
          <button
            onClick={onCancel}
            className="text-muted hover:text-primary p-1 rounded-full hover:bg-hover"
            aria-label="Cancel emergency modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <p className="text-sm text-primary/90 leading-relaxed font-medium">
          You are triggering a high-priority emergency rescue request. Your detected GPS coordinates will be attached to the payload.
        </p>

        <div>
          <label className="block text-xs font-mono font-bold uppercase text-muted mb-2">
            Primary Hazard (Optional):
          </label>
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: 'LANDSLIDE', label: '⛰️ Landslide' },
              { id: 'FLOOD', label: '🌊 Flash Flood' },
              { id: 'PERSON_TRAPPED', label: '🏚️ Trapped' },
              { id: 'OTHER', label: '🚑 Other Medical' },
            ].map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setSelectedCategory(cat.id as IncidentCategory)}
                className={`px-3 py-2 text-xs font-heading font-bold rounded-xl border text-left flex items-center justify-between transition-colors ${
                  selectedCategory === cat.id
                    ? 'bg-[#8E2F2B]/15 text-[#8E2F2B] border-[#8E2F2B]'
                    : 'bg-main text-primary border-border/50 hover:bg-hover'
                }`}
              >
                <span>{cat.label}</span>
                {selectedCategory === cat.id && <CheckCircle2 className="w-3.5 h-3.5 text-[#8E2F2B] ml-1" />}
              </button>
            ))}
          </div>
        </div>

        <div className="pt-2 flex flex-col space-y-2.5">
          <Button
            variant="emergency"
            size="lg"
            fullWidth
            onClick={() => onConfirm(selectedCategory)}
            autoFocus
          >
            SEND EMERGENCY SIGNAL NOW
          </Button>

          <Button variant="ghost" size="md" fullWidth onClick={onCancel}>
            Cancel (Accidental Press)
          </Button>
        </div>
      </div>
    </div>
  );
};
