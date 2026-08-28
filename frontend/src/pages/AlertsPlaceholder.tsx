import React, { useRef, useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { Badge } from '../components/ui/Badge';
import { animatePageEnter } from '../animations/pageTransitions';
import { Bell, Volume2, VolumeX, ShieldAlert } from 'lucide-react';

export const AlertsPlaceholder: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [activeAudioText, setActiveAudioText] = useState<string | null>(null);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const handlePlayTtsAudio = (text: string) => {
    if ('speechSynthesis' in window) {
      if (isPlayingAudio) {
        window.speechSynthesis.cancel();
        setIsPlayingAudio(false);
        setActiveAudioText(null);
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.onend = () => {
        setIsPlayingAudio(false);
        setActiveAudioText(null);
      };
      utterance.onerror = () => {
        setIsPlayingAudio(false);
        setActiveAudioText(null);
      };

      setIsPlayingAudio(true);
      setActiveAudioText(text);
      window.speechSynthesis.speak(utterance);
    } else {
      alert('Speech synthesis API is not supported in this browser environment.');
    }
  };

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-4 font-sans">
      <div className="flex items-center justify-between pb-2 border-b border-border/50">
        <div>
          <span className="text-xs font-mono font-bold text-accent uppercase tracking-widest block">
            PUBLIC SAFETY BROADCAST
          </span>
          <h2 className="text-xl font-heading font-black text-primary uppercase tracking-wide">
            3-Tier Emergency Alerts
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      <div className="flex items-center justify-between p-3.5 rounded-xl bg-surface border border-border/50 text-xs font-mono">
        <div className="flex items-center space-x-2 text-primary">
          <ShieldAlert className="w-4 h-4 text-accent" />
          <span>Multilingual Broadcast: <strong>TEXT + AUDIO SYNTHESIS</strong></span>
        </div>
      </div>

      <div className="space-y-4">
        {/* Critical Evacuation Warning Notice */}
        <Card className="p-5 border-2 border-[#8E2F2B] bg-surface space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <span className="text-xs font-heading font-bold text-[#8E2F2B] uppercase tracking-wider flex items-center">
              <Bell className="w-4 h-4 mr-1.5" /> OFFICIAL EVACUATION WARNING
            </span>
            <Badge level="CRITICAL" />
          </div>

          <h3 className="text-base font-heading font-bold text-primary">
            Landslide Debris Flow Triggered in Upper Reach (Sector 4)
          </h3>

          <p className="text-xs text-primary/90 leading-relaxed font-medium">
            IMD & CrisisCore hydro-sensor threshold breached (180mm rain / 94% soil saturation). Residents in Sector 4 must relocate to High-Ground Community Shelter B immediately. Avoid NH-10 Pass.
          </p>

          <div className="pt-2 flex items-center justify-between border-t border-hover text-[11px] font-mono text-muted">
            <span>Issued: 14 mins ago &bull; Regional Disaster Authority</span>
            
            <button
              onClick={() => handlePlayTtsAudio('Critical Landslide Warning. Upper Reach Sector 4. Residents in Sector 4 should relocate to Community Shelter B immediately.')}
              className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-[#8E2F2B]/10 text-[#8E2F2B] font-bold hover:bg-[#8E2F2B]/20 transition-colors"
            >
              {isPlayingAudio && activeAudioText?.includes('Upper Reach') ? (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Stop Audio</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5" />
                  <span>Play Audio</span>
                </>
              )}
            </button>
          </div>
        </Card>

        {/* High Flash Flood Advisory Notice */}
        <Card className="p-5 border border-[#D88A32] bg-surface space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-heading font-bold text-[#D88A32] uppercase tracking-wider flex items-center">
              <Bell className="w-4 h-4 mr-1.5" /> FLASH FLOOD ADVISORY
            </span>
            <Badge level="HIGH" />
          </div>

          <h3 className="text-base font-heading font-bold text-primary">
            Periyar River Surge Threshold 85% Breached
          </h3>

          <p className="text-xs text-primary/90 leading-relaxed font-medium">
            River water level rising at 0.4m/hr. Avoid low-lying causeways and river crossings in Sector 2 and 3.
          </p>

          <div className="pt-2 flex items-center justify-between border-t border-hover text-[11px] font-mono text-muted">
            <span>Issued: 45 mins ago &bull; Hydro-Sensor Mesh</span>
            
            <button
              onClick={() => handlePlayTtsAudio('Flash Flood Advisory. Periyar River surge threshold 85 percent. Avoid low-lying causeways and river crossings.')}
              className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-[#D88A32]/15 text-[#D88A32] font-bold hover:bg-[#D88A32]/25 transition-colors"
            >
              <Volume2 className="w-3.5 h-3.5" />
              <span>Play Audio</span>
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};
