import React, { useState } from 'react';
import { NetworkIndicator } from '../ui/NetworkIndicator';
import { DataSourceBadge } from '../ui/DataSourceBadge';
import { NetworkStatusType } from '../../types/emergency';
import { TabType } from './BottomNav';
import { Shield, Home, AlertTriangle, Activity, Users, Bell, Globe, Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

interface HeaderProps {
  networkStatus: NetworkStatusType;
  activeTab?: TabType;
  onTabChange?: (tab: TabType) => void;
}

const LANGUAGES = ['English', 'Hindi (हिंदी)', 'Assamese (অসমীয়া)', 'Bengali (বাংলা)', 'Manipuri (ꯃꯏꯇꯩꯂꯣꯟ)', 'Mizo', 'Khasi'];

export const Header: React.FC<HeaderProps> = ({ networkStatus, activeTab = 'home', onTabChange }) => {
  const [currentLang, setCurrentLang] = useState('English');
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const { isDark, toggleTheme } = useTheme();

  const desktopTabs = [
    { id: 'home', label: 'MAP', icon: Home },
    { id: 'incident', label: 'REPORT', icon: AlertTriangle },
    { id: 'status', label: 'SOS STATUS', icon: Activity },
    { id: 'family', label: 'FAMILY', icon: Users },
    { id: 'alerts', label: 'ALERTS', icon: Bell },
  ] as const;

  return (
    <header className="sticky top-0 z-40 bg-surface/95 backdrop-blur-md border-b border-border/50 px-4 py-3 font-sans">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Branding Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-accent text-surface flex items-center justify-center shadow-sm shrink-0">
            <Shield className="w-5 h-5 fill-current" />
          </div>
          <div>
            <h1 className="text-lg font-heading font-black tracking-wider text-primary uppercase leading-none">
              CRISISCORE
            </h1>
            <span className="text-[10px] font-mono text-muted tracking-tight block mt-0.5">
              SIH26001 &bull; LANDSLIDE EARLY WARNING
            </span>
          </div>
        </div>

        {/* Minimal Top Navigation Links (Desktop) */}
        {onTabChange && (
          <nav className="hidden lg:flex items-center space-x-1 bg-main p-1 rounded-2xl border border-border/50">
            {desktopTabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id as TabType)}
                  className={`px-4 py-1.5 rounded-xl text-xs font-heading font-bold transition-all ${
                    isActive
                      ? 'bg-accent text-surface shadow-sm'
                      : 'text-muted hover:text-primary hover:bg-hover'
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>
        )}

        {/* Right Tools: Theme Toggle, Language Selector, Data Badge, Network Indicator */}
        <div className="flex items-center space-x-2 shrink-0">
          
          <button
            onClick={toggleTheme}
            className="p-1.5 sm:p-2 rounded-lg text-primary hover:bg-hover transition-colors flex items-center justify-center"
            aria-label="Toggle dark mode"
          >
            {isDark ? <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-accent" /> : <Moon className="w-4 h-4 sm:w-5 sm:h-5 text-muted" />}
          </button>

          {/* Language Selector */}
          <div className="relative">
            <button
              onClick={() => setShowLangDropdown(!showLangDropdown)}
              className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-main border border-border/50 text-xs font-mono font-bold text-primary hover:bg-hover"
            >
              <Globe className="w-3.5 h-3.5 text-accent" />
              <span className="hidden sm:inline">{currentLang}</span>
            </button>

            {showLangDropdown && (
              <div className="absolute right-0 mt-2 w-44 bg-surface border border-border rounded-xl shadow-xl py-1 z-50 text-xs font-mono">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang}
                    onClick={() => {
                      setCurrentLang(lang.split(' ')[0]);
                      setShowLangDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 hover:bg-hover ${
                      currentLang === lang.split(' ')[0] ? 'font-bold text-accent' : 'text-primary'
                    }`}
                  >
                    {lang}
                  </button>
                ))}
              </div>
            )}
          </div>

          <DataSourceBadge type="synthetic" size="sm" />
          <NetworkIndicator status={networkStatus} />
        </div>
      </div>
    </header>
  );
};
