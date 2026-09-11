import React, { useState, useRef, useEffect } from 'react';
import { NetworkIndicator } from '../ui/NetworkIndicator';
import { DataSourceBadge } from '../ui/DataSourceBadge';
import { NetworkStatusType } from '../../types/emergency';
import { TabType } from './BottomNav';
import { useTranslation } from '../../i18n/LanguageContext';
import { useAudioAlert } from '../../hooks/useAudioAlert';
import { useClickOutside } from '../../hooks/useClickOutside';
import { QrCode, Shield, ShieldCheck, Globe, Volume2, VolumeX, LifeBuoy } from 'lucide-react';
import { OperationsAuthModal } from './OperationsAuthModal';
import { getAuthInfo, AuthInfo } from '../../services/api';

interface HeaderProps {
  networkStatus: NetworkStatusType;
  activeTab?: TabType;
  onTabChange?: (tab: TabType) => void;
  onOpenQrScanner?: () => void;
  onOpenHelp?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ networkStatus, onOpenQrScanner, onOpenHelp }) => {
  const { language, setLanguage, languages, t } = useTranslation();
  const { audioEnabled, toggleAudioEnabled } = useAudioAlert();
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authInfo, setAuthInfo] = useState<AuthInfo>(() => getAuthInfo());
  const langDropdownRef = useRef<HTMLDivElement>(null);

  useClickOutside(langDropdownRef, () => setShowLangDropdown(false), showLangDropdown);

  useEffect(() => {
    const handleAuthChange = () => {
      setAuthInfo(getAuthInfo());
    };
    const handleOpenAuth = () => {
      setIsAuthModalOpen(true);
    };
    window.addEventListener('crisiscore-auth-change', handleAuthChange);
    window.addEventListener('open-operations-auth', handleOpenAuth);
    return () => {
      window.removeEventListener('crisiscore-auth-change', handleAuthChange);
      window.removeEventListener('open-operations-auth', handleOpenAuth);
    };
  }, []);

  const activeLangObj = languages.find((l) => l.code === language) || languages[0];
  const isOpsUser = authInfo.status === 'authenticated';
  const role = authInfo.role;

  const opsBadgeText =
    authInfo.status === 'bootstrapping'
      ? 'OPS: ...'
      : authInfo.status === 'unauthenticated'
      ? `OPS: ${t('common.login') || 'LOGIN'}`
      : authInfo.status === 'access_required'
      ? 'OPS: ACCESS REQ'
      : role === 'officer'
      ? `OPS: ${t('ops.badgeOfficer')}`
      : role === 'admin'
      ? `OPS: ${t('ops.badgeAdmin')}`
      : `OPS: ${role ? role.toUpperCase() : t('common.login') || 'LOGIN'}`;

  const opsBadgeColor =
    authInfo.status === 'authenticated'
      ? 'bg-[#23483A]/10 border-[#23483A]/30 text-[#23483A] hover:bg-[#23483A]/20'
      : authInfo.status === 'access_required'
      ? 'bg-[#8E2F2B]/15 border-[#8E2F2B]/40 text-[#8E2F2B] hover:bg-[#8E2F2B]/25'
      : 'bg-[#D88A32]/15 border-[#D88A32]/40 text-[#965C22] hover:bg-[#D88A32]/25';

  return (
    <header className="sticky top-0 z-40 bg-[#FAF9F3]/95 backdrop-blur-md border-b border-[#C7B89B]/50 px-3 sm:px-4 py-3 pt-[calc(0.75rem+env(safe-area-inset-top,0px))] font-sans">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-2">
        
        {/* Branding Title */}
        <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
          <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-[#23483A] text-[#FAF9F3] flex items-center justify-center shadow-sm shrink-0">
            <Shield className="w-4 h-4 sm:w-5 sm:h-5 fill-current" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-heading font-black tracking-wider text-[#202622] uppercase leading-none px-1 py-0.5 sm:px-1.5">
              SAMVEDNA
            </h1>
            <span className="text-[9px] sm:text-[10px] font-mono text-[#536A72] tracking-tight block mt-0.5 uppercase">
              {t('nav.subtitle')}
            </span>
          </div>
        </div>

        {/* Right Tools: Audio Alert Section, Language Selector, Data Badge, Network Indicator, Volunteer Verification */}
        <div className="flex items-center space-x-1.5 sm:space-x-2 shrink-0 overflow-x-auto max-w-[65%] sm:max-w-none py-0.5 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {/* Audio Alert Section (Separated from main navigation by ~28-32px spacing & border) */}
          <div className="hidden md:flex items-center pl-3 ml-3 sm:ml-6 sm:pl-6 border-l border-[#C7B89B]/50">
            <button
              onClick={() => {
                setShowLangDropdown(false);
                toggleAudioEnabled();
              }}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-mono font-bold border transition-colors cursor-pointer ${
                audioEnabled ? 'bg-[#23483A]/10 text-[#23483A] border-[#23483A]/30' : 'bg-[#FAF9F3] text-[#536A72] border-[#C7B89B]/50'
              }`}
              title={audioEnabled ? t('audio.enabled') : t('audio.disabled')}
            >
              {audioEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
              <span className="hidden xl:inline">{audioEnabled ? t('audio.enabled') : t('audio.disabled')}</span>
            </button>
          </div>

          {/* Language Selector Dropdown Container with Click-Outside Detection */}
          <div ref={langDropdownRef} className="relative">
            <button
              onClick={() => setShowLangDropdown(!showLangDropdown)}
              className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-[#F4F1E8] border border-[#C7B89B]/50 text-xs font-mono font-bold text-[#202622] hover:bg-[#E8E6DC] transition-colors cursor-pointer"
            >
              <Globe className="w-3.5 h-3.5 text-[#23483A]" />
              <span className="hidden sm:inline">{activeLangObj.nativeName}</span>
            </button>

            {showLangDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-[#FAF9F3] border border-[#C7B89B] rounded-xl shadow-xl py-1 z-50 text-xs font-mono">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => {
                      setLanguage(lang.code);
                      setShowLangDropdown(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 hover:bg-[#E8E6DC] flex items-center justify-between cursor-pointer ${
                      language === lang.code ? 'font-bold text-[#23483A] bg-[#23483A]/10' : 'text-[#202622]'
                    }`}
                  >
                    <span>{lang.nativeName}</span>
                    <span className="text-[10px] text-[#536A72]">{lang.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <DataSourceBadge type={isOpsUser ? 'live' : 'synthetic'} size="sm" />
          <NetworkIndicator status={networkStatus} />

          {/* Operations Authorization Status & Command Access */}
          <button
            onClick={() => setIsAuthModalOpen(true)}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono font-bold transition-colors cursor-pointer shadow-sm ${opsBadgeColor}`}
            title="Operations Authentication"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline uppercase">{opsBadgeText}</span>
          </button>

          {/* Dedicated Visually-Separated Volunteer Verification & Emergency Help Section */}
          <div className="pl-3 ml-3 sm:ml-4 sm:pl-4 border-l border-[#C7B89B]/60 flex items-center space-x-2 shrink-0">
            {onOpenHelp && (
              <button
                onClick={onOpenHelp}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#8E2F2B] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#722421] transition-all cursor-pointer shadow-sm tactile-press"
                title={t('nav.help')}
              >
                <LifeBuoy className="w-4 h-4 text-[#FAF9F3] animate-pulse" />
                <span className="hidden sm:inline">{t('nav.help')}</span>
              </button>
            )}

            {onOpenQrScanner && (
              <button
                onClick={onOpenQrScanner}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#1b382d] transition-all cursor-pointer shadow-sm tactile-press"
                title={t('qr.verifyTitle')}
              >
                <QrCode className="w-4 h-4 text-[#FAF9F3]" />
                <span className="hidden md:inline">{t('qr.verifyTitle')}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <OperationsAuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthChange={() => setAuthInfo(getAuthInfo())}
      />
    </header>
  );
};
