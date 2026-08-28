import React from 'react';
import { useAudioAlert } from '../../hooks/useAudioAlert';
import { useTranslation } from '../../i18n/LanguageContext';
import { Volume2, VolumeX, Pause, Play, Square } from 'lucide-react';

interface AudioAlertButtonProps {
  text: string;
  className?: string;
  size?: 'sm' | 'md';
}

export const AudioAlertButton: React.FC<AudioAlertButtonProps> = ({
  text,
  className = '',
  size = 'md',
}) => {
  const { t } = useTranslation();
  const {
    isSupported,
    isPlaying,
    isPaused,
    audioEnabled,
    currentText,
    speak,
    pause,
    resume,
    stop,
  } = useAudioAlert();

  if (!isSupported) {
    return (
      <span className="text-[10px] font-mono text-[#536A72] italic">
        {t('audio.unavailable')}
      </span>
    );
  }

  if (!audioEnabled) {
    return null;
  }

  const isCurrentSpeaking = (isPlaying || isPaused) && currentText === text;

  const sizeClasses =
    size === 'sm'
      ? 'px-2 py-1 text-[11px]'
      : 'px-3 py-1.5 text-xs';

  return (
    <div className={`inline-flex items-center space-x-1 font-sans ${className}`} role="region" aria-label="Audio alert controls">
      {!isCurrentSpeaking ? (
        <button
          type="button"
          onClick={() => speak(text)}
          className={`inline-flex items-center space-x-1.5 rounded-xl font-heading font-bold bg-[#FAF9F3] text-[#23483A] border border-[#23483A]/30 hover:bg-[#23483A] hover:text-[#FAF9F3] transition-all shadow-sm cursor-pointer tactile-press ${sizeClasses}`}
          aria-label={`${t('audio.listen')}: ${text.slice(0, 30)}...`}
        >
          <Volume2 className="w-3.5 h-3.5 shrink-0" />
          <span>{t('audio.listen')}</span>
        </button>
      ) : (
        <div className="inline-flex items-center space-x-1 bg-[#23483A] text-[#FAF9F3] p-1 rounded-xl shadow-md font-mono text-xs animate-fade-in">
          <div className="flex items-center space-x-1 px-2">
            <Volume2 className={`w-3.5 h-3.5 ${isPlaying ? 'animate-bounce' : ''}`} />
            <span className="font-bold">
              {isPlaying ? t('audio.playing') : t('audio.paused')}
            </span>
          </div>

          {isPlaying ? (
            <button
              type="button"
              onClick={pause}
              className="p-1 rounded-lg bg-white/20 hover:bg-white/30 text-white cursor-pointer"
              aria-label={t('audio.paused')}
              title={t('audio.paused')}
            >
              <Pause className="w-3 h-3" />
            </button>
          ) : (
            <button
              type="button"
              onClick={resume}
              className="p-1 rounded-lg bg-white/20 hover:bg-white/30 text-white cursor-pointer"
              aria-label={t('audio.resume')}
              title={t('audio.resume')}
            >
              <Play className="w-3 h-3 fill-current" />
            </button>
          )}

          <button
            type="button"
            onClick={stop}
            className="p-1 rounded-lg bg-[#8E2F2B] hover:bg-[#a83833] text-white cursor-pointer"
            aria-label={t('audio.stop')}
            title={t('audio.stop')}
          >
            <Square className="w-3 h-3 fill-current" />
          </button>
        </div>
      )}
    </div>
  );
};
