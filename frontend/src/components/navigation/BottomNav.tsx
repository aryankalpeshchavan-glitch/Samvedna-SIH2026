import React from 'react';
import { Home, AlertTriangle, Activity, Users, Bell, LucideIcon } from 'lucide-react';
import { SosState } from '../../types/emergency';

export type TabType = 'home' | 'incident' | 'status' | 'family' | 'alerts';

interface BottomNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  sosState: SosState;
}

interface TabItem {
  id: TabType;
  label: string;
  icon: LucideIcon;
  badge?: boolean;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange, sosState }) => {
  const tabs: TabItem[] = [
    { id: 'home', label: 'Map', icon: Home },
    { id: 'incident', label: 'Report', icon: AlertTriangle },
    { id: 'status', label: 'SOS Status', icon: Activity, badge: sosState !== 'IDLE' },
    { id: 'family', label: 'Family', icon: Users },
    { id: 'alerts', label: 'Alerts', icon: Bell },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#FAF9F3]/95 backdrop-blur-md border-t border-[#C7B89B]/50 py-1.5 px-2 font-sans">
      <div className="max-w-xl mx-auto flex items-center justify-around">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`relative flex flex-col items-center justify-center py-1.5 px-3 rounded-xl touch-target-lg transition-colors focus:outline-none ${
                isActive
                  ? 'text-[#23483A] font-bold bg-[#E8E6DC]'
                  : 'text-[#536A72] hover:text-[#202622]'
              }`}
              aria-label={`Navigate to ${tab.label}`}
            >
              <div className="relative">
                <Icon className="w-5 h-5 mb-0.5" />
                {tab.badge && (
                  <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-[#8E2F2B] animate-ping" />
                )}
              </div>
              <span className="text-[11px] font-heading font-semibold tracking-tight">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
