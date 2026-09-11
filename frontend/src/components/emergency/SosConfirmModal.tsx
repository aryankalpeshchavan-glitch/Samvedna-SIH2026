import React, { useRef, useEffect } from 'react';
import { animateModalEntrance } from '../../animations/sosAnimations';
import { Button } from '../ui/Button';
import { AlertOctagon, X, CheckCircle2 } from 'lucide-react';
import { IncidentCategory } from '../../types/emergency';
import { useTranslation } from '../../i18n/LanguageContext';
import { ModalPortal } from '../ui/ModalPortal';

interface SosConfirmModalProps {
  onConfirm: (category?: IncidentCategory) => void;
  onCancel: () => void;
}

export const SosConfirmModal: React.FC<SosConfirmModalProps> = ({ onConfirm, onCancel }) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const [selectedCategory, setSelectedCategory] = React.useState<IncidentCategory | undefined>(undefined);
  const { t } = useTranslation();

  useEffect(() => {
    animateModalEntrance(modalRef.current);
  }, []);

  return (
    <ModalPortal onClose={onCancel}>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/70 backdrop-blur-sm font-sans"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onClick={onCancel}
      >
        <div
          ref={modalRef}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-md bg-[#FAF9F3] border-2 border-[#8E2F2B] rounded-3xl p-6 shadow-2xl text-left space-y-4"
        >
        <div className="flex items-start justify-between pb-3 border-b border-[#E8E6DC]">
          <div className="flex items-center space-x-2 text-[#8E2F2B]">
            <AlertOctagon className="w-6 h-6 shrink-0" />
            <h2 id="modal-title" className="text-xl font-heading font-black tracking-wide text-[#202622] uppercase">
              {t('sos.confirmTitle')}
            </h2>
          </div>
          <button
            onClick={onCancel}
            className="text-[#536A72] hover:text-[#202622] p-1 rounded-full hover:bg-[#E8E6DC]"
            aria-label="Cancel emergency modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <p className="text-sm text-[#202622]/90 leading-relaxed font-medium">
          {t('sos.confirmWarning')}
        </p>

        <div>
          <label className="block text-xs font-mono font-bold uppercase text-[#536A72] mb-2">
            {t('sos.selectCategoryOptional')}
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
                    : 'bg-[#F4F1E8] text-[#202622] border-[#C7B89B]/50 hover:bg-[#E8E6DC]'
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
            {t('sos.confirmButton')}
          </Button>

          <Button variant="ghost" size="md" fullWidth onClick={onCancel}>
            {t('sos.cancelButton')}
          </Button>
        </div>
      </div>
      </div>
    </ModalPortal>
  );
};
