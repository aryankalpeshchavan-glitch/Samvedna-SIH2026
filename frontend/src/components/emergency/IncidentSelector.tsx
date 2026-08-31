import React, { useRef, useEffect } from 'react';
import { IncidentCategory } from '../../types/emergency';
import { Card } from '../ui/Card';
import { animateStaggerIn } from '../../animations/pageTransitions';
import { Waves, Mountain, UserX, Stethoscope, Building2, Flame, AlertCircle } from 'lucide-react';

interface IncidentItem {
  id: IncidentCategory;
  title: string;
  subtitle: string;
  icon: React.ElementType;
  color: string;
}

const INCIDENTS: IncidentItem[] = [
  {
    id: 'LANDSLIDE',
    title: 'Landslide / Mudslide',
    subtitle: 'Debris flow, slope collapse, road block',
    icon: Mountain,
    color: 'text-amber-400 border-amber-500/40 bg-amber-950/20',
  },
  {
    id: 'FLASH_FLOOD',
    title: 'Flash Flood',
    subtitle: 'Rapid water rise, submerged path, river surge',
    icon: Waves,
    color: 'text-blue-400 border-blue-500/40 bg-blue-950/20',
  },
  {
    id: 'PERSON_TRAPPED',
    title: 'Person Trapped',
    subtitle: 'Under collapse, isolated, unable to evacuate',
    icon: UserX,
    color: 'text-red-400 border-red-500/40 bg-red-950/20',
  },
  {
    id: 'MEDICAL_EMERGENCY',
    title: 'Medical Emergency',
    subtitle: 'Severe injury, trauma, unresponsive',
    icon: Stethoscope,
    color: 'text-emerald-400 border-emerald-500/40 bg-emerald-950/20',
  },
  {
    id: 'BUILDING_DAMAGE',
    title: 'Structure Damage',
    subtitle: 'Wall crack, bridge breach, roof collapse',
    icon: Building2,
    color: 'text-purple-400 border-purple-500/40 bg-purple-950/20',
  },
  {
    id: 'FIRE',
    title: 'Fire Hazard',
    subtitle: 'Structure fire, electrical spark, forest fire',
    icon: Flame,
    color: 'text-orange-400 border-orange-500/40 bg-orange-950/20',
  },
  {
    id: 'OTHER',
    title: 'Other Multi-Hazard',
    subtitle: 'Power line down, gas leak, hazardous material',
    icon: AlertCircle,
    color: 'text-gray-300 border-gray-500/40 bg-gray-900/30',
  },
];

interface IncidentSelectorProps {
  onSelect: (category: IncidentCategory) => void;
  selectedCategory?: IncidentCategory;
}

export const IncidentSelector: React.FC<IncidentSelectorProps> = ({ onSelect, selectedCategory }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      const cards = containerRef.current.querySelectorAll('.incident-card');
      animateStaggerIn(cards as unknown as ArrayLike<HTMLElement>);
    }
  }, []);

  return (
    <div ref={containerRef} className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4">
      {INCIDENTS.map((item) => {
        const Icon = item.icon;
        const isSelected = selectedCategory === item.id;

        return (
          <Card
            key={item.id}
            interactive
            active={isSelected}
            onClick={() => onSelect(item.id)}
            className={`incident-card flex items-start space-x-3.5 p-4 border transition-all ${
              isSelected ? 'border-red-500 bg-red-950/40 ring-2 ring-red-500/50' : ''
            }`}
          >
            <div className={`p-2.5 rounded-xl border shrink-0 ${item.color}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className="text-base font-bold text-white font-mono tracking-tight">
                  {item.title}
                </h4>
              </div>
              <p className="text-xs text-gray-400 font-medium mt-0.5 leading-snug">
                {item.subtitle}
              </p>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
