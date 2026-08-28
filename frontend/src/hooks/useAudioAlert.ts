import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from '../i18n/LanguageContext';
import { LanguageCode } from '../i18n/translations';

const AUDIO_SETTING_KEY = 'crisiscore_audio_alerts_enabled';

// BCP 47 language tag mapping for Web Speech API
const LANG_TAG_MAP: Record<LanguageCode, string[]> = {
  en: ['en-IN', 'en-US', 'en-GB', 'en'],
  hi: ['hi-IN', 'hi'],
  bn: ['bn-IN', 'bn-BD', 'bn'],
  as: ['as-IN', 'hi-IN', 'en-IN'], // Fallback to hi-IN or en-IN if native Assamese voice is missing
  mni: ['mni-IN', 'hi-IN', 'en-IN'],
  lus: ['lus-IN', 'hi-IN', 'en-IN'],
  kha: ['kha-IN', 'en-IN', 'hi-IN'],
};

export interface UseAudioAlertReturn {
  isSupported: boolean;
  isPlaying: boolean;
  isPaused: boolean;
  audioEnabled: boolean;
  currentText: string | null;
  toggleAudioEnabled: () => void;
  speak: (text: string) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
}

export function useAudioAlert(): UseAudioAlertReturn {
  const { language } = useTranslation();
  const [isSupported, setIsSupported] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentText, setCurrentText] = useState<string | null>(null);

  const [audioEnabled, setAudioEnabled] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem(AUDIO_SETTING_KEY);
      return saved === null ? true : saved === 'true';
    } catch {
      return true;
    }
  });

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);
    }
  }, []);

  const toggleAudioEnabled = useCallback(() => {
    setAudioEnabled((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(AUDIO_SETTING_KEY, String(next));
      } catch {
        // Ignore storage error
      }
      if (!next && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        setIsPlaying(false);
        setIsPaused(false);
        setCurrentText(null);
      }
      return next;
    });
  }, []);

  const findBestVoice = useCallback((langCode: LanguageCode): SpeechSynthesisVoice | null => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    if (voices.length === 0) return null;

    const preferredTags = LANG_TAG_MAP[langCode] || ['en-IN', 'en'];

    for (const tag of preferredTags) {
      const found = voices.find((v) => v.lang.toLowerCase().startsWith(tag.toLowerCase()));
      if (found) return found;
    }

    return voices[0] || null;
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!isSupported || !audioEnabled) return;

      const synth = window.speechSynthesis;
      synth.cancel(); // Stop any ongoing speech

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.92; // Slightly slower for emergency accessibility clarity
      utterance.pitch = 1.0;

      const bestVoice = findBestVoice(language);
      if (bestVoice) {
        utterance.voice = bestVoice;
        utterance.lang = bestVoice.lang;
      }

      utterance.onstart = () => {
        setIsPlaying(true);
        setIsPaused(false);
        setCurrentText(text);
      };

      utterance.onend = () => {
        setIsPlaying(false);
        setIsPaused(false);
        setCurrentText(null);
      };

      utterance.onerror = (e) => {
        // SpeechSynthesis error fallback
        console.warn('[AudioAlert] SpeechSynthesis error:', e);
        setIsPlaying(false);
        setIsPaused(false);
        setCurrentText(null);
      };

      synth.speak(utterance);
    },
    [isSupported, audioEnabled, language, findBestVoice]
  );

  const pause = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.pause();
    setIsPaused(true);
    setIsPlaying(false);
  }, [isSupported]);

  const resume = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.resume();
    setIsPaused(false);
    setIsPlaying(true);
  }, [isSupported]);

  const stop = useCallback(() => {
    if (!isSupported) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
    setCurrentText(null);
  }, [isSupported]);

  return {
    isSupported,
    isPlaying,
    isPaused,
    audioEnabled,
    currentText,
    toggleAudioEnabled,
    speak,
    pause,
    resume,
    stop,
  };
}
