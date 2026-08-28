import React, { useRef, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { DataSourceBadge } from '../components/ui/DataSourceBadge';
import { animatePageEnter } from '../animations/pageTransitions';
import { Users, ShieldCheck, Heart, UserPlus, AlertCircle } from 'lucide-react';

export const FamilyPlaceholder: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    animatePageEnter(containerRef.current);
  }, []);

  return (
    <div ref={containerRef} className="pb-24 pt-4 px-4 max-w-xl mx-auto space-y-4 font-sans">
      <div className="flex items-center justify-between pb-2 border-b border-border/50">
        <div>
          <span className="text-xs font-mono font-bold text-accent uppercase tracking-widest block">
            COMMUNITY MESH NETWORK
          </span>
          <h2 className="text-xl font-heading font-black text-primary uppercase tracking-wide">
            Family Safety Net
          </h2>
        </div>
        <DataSourceBadge type="synthetic" />
      </div>

      <Card className="p-5 border-accent/40 bg-surface">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-3 rounded-2xl bg-accent/10 text-accent">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-heading font-bold text-primary">Family Safety Status</h3>
            <p className="text-xs text-muted">Offline SMS status checking for registered family circle.</p>
          </div>
        </div>
      </Card>

      <div className="space-y-3">
        {[
          { name: 'Priya Sharma (Spouse)', status: 'SAFE', location: 'Community Shelter A', time: '10m ago', icon: ShieldCheck, color: 'text-accent', bg: 'bg-accent/10' },
          { name: 'Aarav Sharma (Son)', status: 'SAFE', location: 'School High Ground', time: '15m ago', icon: Heart, color: 'text-accent', bg: 'bg-accent/10' },
          { name: 'Sunil Sharma (Father)', status: 'UNVERIFIED', location: 'Last seen: Sector 4 Pass', time: '42m ago', icon: AlertCircle, color: 'text-[#D88A32]', bg: 'bg-[#D88A32]/10' },
        ].map((item, idx) => (
          <Card key={idx} className="flex items-center justify-between p-4 bg-surface">
            <div className="flex items-center space-x-3">
              <div className={`p-2.5 rounded-xl ${item.bg} ${item.color}`}>
                <item.icon className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-heading font-bold text-primary">{item.name}</h4>
                <span className="text-xs text-muted">{item.location} &bull; {item.time}</span>
              </div>
            </div>
            <span className={`text-xs font-mono font-bold px-2.5 py-1 rounded-md border ${
              item.status === 'SAFE' ? 'bg-accent/10 text-accent border-accent/30' : 'bg-[#D88A32]/15 text-[#D88A32] border-[#D88A32]/30'
            }`}>
              {item.status}
            </span>
          </Card>
        ))}
      </div>

      <button className="w-full p-4 rounded-2xl border-2 border-dashed border-border text-xs font-heading font-bold text-muted hover:text-primary hover:border-accent flex items-center justify-center space-x-2 transition-colors">
        <UserPlus className="w-4 h-4" />
        <span>+ Add Family Member (SMS Sync)</span>
      </button>
    </div>
  );
};
