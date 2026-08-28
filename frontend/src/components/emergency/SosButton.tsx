import React, { useRef } from 'react';
import { animateSosPress } from '../../animations/sosAnimations';
import { useTranslation } from '../../i18n/LanguageContext';
import { AlertOctagon } from 'lucide-react';

interface SosButtonProps {
  onTrigger: () => void;
  disabled?: boolean;
}

export const SosButton: React.FC<SosButtonProps> = ({ onTrigger, disabled = false }) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const { t } = useTranslation();

  const handleClick = () => {
    if (disabled) return;
    animateSosPress(buttonRef.current, () => {
      onTrigger();
    });
  };

  return (
    <div className="flex flex-col items-center justify-center my-2 font-sans">
      <button
        ref={buttonRef}
        onClick={handleClick}
        disabled={disabled}
        className="w-full py-4 px-6 rounded-2xl bg-[#8E2F2B] hover:bg-[#722522] active:bg-[#581c1a] text-[#FAF9F3] flex items-center justify-center space-x-3 shadow-md tactile-press focus:outline-none focus-visible:ring-4 focus-visible:ring-[#23483A] transition-colors cursor-pointer"
        aria-label="SOS Get Help. Initiate priority rescue request."
      >
        <AlertOctagon className="w-6 h-6 text-[#FAF9F3] shrink-0" />
        <div className="text-left">
          <span className="text-lg font-heading font-black tracking-wider uppercase block leading-none">
            {t('home.triggerSos')}
          </span>
          <span className="text-[11px] font-mono text-[#FAF9F3]/80 uppercase tracking-widest block mt-0.5">
            {t('home.sosDescription')}
          </span>
        </div>
      </button>
    </div>
  );
};
