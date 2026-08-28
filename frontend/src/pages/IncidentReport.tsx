import React, { useState, useRef, useEffect } from 'react';
import { IncidentCategory, SeverityLevel } from '../types/emergency';
import { Button } from '../components/ui/Button';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { animatePageEnter } from '../animations/pageTransitions';
import { Camera, Send, CheckCircle2, Mountain, Waves, UserX, Stethoscope, Building2, Flame, AlertCircle, MapPin, Image } from 'lucide-react';

interface IncidentReportProps {
  onSubmit: (category: IncidentCategory, severity: SeverityLevel, note: string) => void;
}

const REPORT_OPTIONS: { id: IncidentCategory; label: string; icon: React.ElementType }[] = [
  { id: 'LANDSLIDE', label: 'Landslide', icon: Mountain },
  { id: 'SLOPE_CRACK', label: 'Slope Crack', icon: AlertCircle },
  { id: 'ROAD_BLOCKED', label: 'Road Blocked', icon: Building2 },
  { id: 'FLOOD', label: 'Flash Flood', icon: Waves },
  { id: 'BUILDING_DAMAGE', label: 'Structure Damage', icon: Building2 },
  { id: 'PERSON_TRAPPED', label: 'Person Trapped', icon: UserX },
  { id: 'OTHER', label: 'Other Hazard', icon: Stethoscope },
];

export const IncidentReport: React.FC<IncidentReportProps> = ({ onSubmit }) => {
  const [selectedCat, setSelectedCat] = useState<IncidentCategory>('LANDSLIDE');
  const [severity, setSeverity] = useState<SeverityLevel>('WATCH');
  const [note, setNote] = useState('');
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const url = URL.createObjectURL(file);
      setPhotoPreview(url);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(selectedCat, severity, note);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="pb-24 pt-8 px-4 max-w-xl mx-auto text-center space-y-4 font-sans">
        <div className="w-16 h-16 rounded-full bg-accent/10 border-2 border-accent text-accent flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-10 h-10" />
        </div>
        <h2 className="text-2xl font-heading font-black text-primary">Hazard Report Transmitted</h2>
        <p className="text-sm text-primary/80 leading-relaxed font-medium">
          Your field observation for <strong className="text-accent font-mono">{selectedCat.replace('_', ' ')}</strong> has been pinned to the local community intelligence map.
        </p>
        <div className="pt-4">
          <Button variant="secondary" onClick={() => setSubmitted(false)}>
            Submit Another Field Observation
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-6 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border/50">
        <div>
          <span className="text-xs font-mono font-bold text-accent uppercase tracking-widest block">
            CITIZEN COMMUNITY INTELLIGENCE
          </span>
          <h2 className="text-xl font-heading font-black text-primary uppercase tracking-wide">
            Report Something
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* 1. Category Selection Grid */}
        <div>
          <label className="block text-xs font-mono font-bold text-muted uppercase tracking-wider mb-2">
            1. Select Incident Type:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
            {REPORT_OPTIONS.map((item) => {
              const Icon = item.icon;
              const isSelected = selectedCat === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedCat(item.id)}
                  className={`p-3 rounded-2xl border text-left flex flex-col justify-between transition-all tactile-press ${
                    isSelected
                      ? 'bg-accent text-surface border-accent shadow-md'
                      : 'bg-surface text-primary border-border/50 hover:bg-hover'
                  }`}
                >
                  <Icon className={`w-5 h-5 mb-2 ${isSelected ? 'text-surface' : 'text-accent'}`} />
                  <span className="text-xs font-heading font-bold">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Photo Upload */}
        <div>
          <label className="block text-xs font-mono font-bold text-muted uppercase tracking-wider mb-2">
            2. Photo Evidence (Optional):
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handlePhotoUpload}
            className="hidden"
          />
          <div
            onClick={() => fileInputRef.current?.click()}
            className="p-4 rounded-2xl border-2 border-dashed border-border bg-surface hover:bg-hover cursor-pointer flex flex-col items-center justify-center text-center transition-colors"
          >
            {photoPreview ? (
              <div className="relative w-full h-32 rounded-xl overflow-hidden">
                <img src={photoPreview} alt="Upload Preview" className="w-full h-full object-cover" />
                <span className="absolute bottom-2 right-2 px-2 py-1 bg-primary/80 text-white text-[10px] rounded font-mono">
                  Photo Attached
                </span>
              </div>
            ) : (
              <>
                <Camera className="w-6 h-6 text-accent mb-1" />
                <span className="text-xs font-heading font-bold text-primary">Take Photo or Upload Image</span>
                <span className="text-[10px] text-muted font-mono mt-0.5">JPEG, PNG up to 10MB</span>
              </>
            )}
          </div>
        </div>

        {/* 3. Location Auto Detection */}
        <div className="p-3 rounded-xl bg-surface border border-border/50 text-xs font-mono text-muted flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-accent" />
            <span>GPS Location: <strong className="text-primary">Auto-Detected Coordinates Attached</strong></span>
          </div>
          <span className="text-accent font-bold">26.14° N, 91.73° E</span>
        </div>

        {/* 4. Severity Toggles */}
        <div>
          <label className="block text-xs font-mono font-bold text-muted uppercase tracking-wider mb-2">
            4. Observed Severity:
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'LOW', label: 'Small' },
              { id: 'WATCH', label: 'Moderate' },
              { id: 'CRITICAL', label: 'Severe' },
            ].map((lvl) => (
              <button
                key={lvl.id}
                type="button"
                onClick={() => setSeverity(lvl.id as SeverityLevel)}
                className={`py-2.5 text-xs font-heading font-bold rounded-xl border transition-colors ${
                  severity === lvl.id
                    ? 'bg-accent text-surface border-accent'
                    : 'bg-surface text-primary border-border/50 hover:bg-hover'
                }`}
              >
                {lvl.label}
              </button>
            ))}
          </div>
        </div>

        {/* 5. Optional Note */}
        <div>
          <label className="block text-xs font-mono font-bold text-muted uppercase tracking-wider mb-2">
            5. Situation Description (Optional):
          </label>
          <textarea
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Debris flow blocking main road near bridge 4. 2 vehicles stranded."
            className="w-full p-3 rounded-xl bg-surface border border-border text-sm text-primary placeholder-muted/60 focus:border-accent focus:outline-none"
          />
        </div>

        <Button variant="secondary" size="lg" fullWidth type="submit">
          <Send className="w-4 h-4 mr-2" />
          SEND REPORT TO COMMUNITY MAP
        </Button>
      </form>
    </div>
  );
};
