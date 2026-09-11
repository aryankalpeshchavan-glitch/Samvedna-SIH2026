import React, { useState } from 'react';
import { X, ShieldCheck, Lock, Phone, AlertTriangle, CheckCircle2, LogOut } from 'lucide-react';
import { login, logout, getUserRole } from '../../services/api';
import { ModalPortal } from '../ui/ModalPortal';


interface OperationsAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthChange?: () => void;
}

export const OperationsAuthModal: React.FC<OperationsAuthModalProps> = ({
  isOpen,
  onClose,
  onAuthChange,
}) => {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const currentRole = getUserRole();

  if (!isOpen) return null;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone || !password) {
      setError('Please provide phone and password.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(phone.trim(), password);
      if (onAuthChange) onAuthChange();
      onClose();
    } catch (err: any) {
      const msg = err?.message || 'Authentication failed';
      if (msg.includes('401') || msg.toLowerCase().includes('credential')) {
        setError('Invalid credentials. Please verify your phone and password.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    if (onAuthChange) onAuthChange();
    onClose();
  };

  return (
    <ModalPortal onClose={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="operations-auth-modal-title"
        onClick={onClose}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/60 backdrop-blur-sm animate-in fade-in duration-200"
      >
      <div
        className="w-full max-w-md bg-[#FAF9F3] border border-[#C7B89B] rounded-3xl shadow-2xl overflow-hidden flex flex-col font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 bg-[#F4F1E8] border-b border-[#C7B89B]/50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-[#23483A] text-[#FAF9F3] flex items-center justify-center shadow-sm shrink-0">
              <ShieldCheck className="w-5 h-5 fill-current" />
            </div>
            <div>
              <h2 id="operations-auth-modal-title" className="text-sm font-heading font-black tracking-wider text-[#202622] uppercase">
                OPERATIONS AUTHENTICATION
              </h2>
              <span className="text-[10px] font-mono text-[#536A72] block">
                Authorized Command & Tactical Dashboard
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#536A72] hover:text-[#202622] hover:bg-[#E8E6DC] transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Current Authorization Status */}
          <div className="p-4 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono font-bold text-[#536A72] uppercase tracking-wider">
                Current Authorization
              </span>
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md uppercase ${
                  currentRole === 'admin'
                    ? 'bg-[#23483A] text-[#FAF9F3]'
                    : currentRole === 'officer'
                    ? 'bg-[#23483A]/80 text-[#FAF9F3]'
                    : currentRole === 'citizen'
                    ? 'bg-[#D88A32] text-white'
                    : 'bg-[#C7B89B] text-[#202622]'
                }`}
              >
                {currentRole ? `Role: ${currentRole}` : 'Unauthenticated'}
              </span>
            </div>

            {currentRole === 'admin' && (
              <p className="text-xs text-[#23483A] font-medium flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-[#23483A]" />
                <span>Full operational & simulation access granted via backend RBAC.</span>
              </p>
            )}

            {currentRole === 'officer' && (
              <p className="text-xs text-[#23483A] font-medium flex items-center space-x-1.5">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-[#23483A]" />
                <span>Operational officer access granted. What-If simulations enabled.</span>
              </p>
            )}

            {currentRole === 'citizen' && (
              <div className="p-3 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-[#8E2F2B] text-xs font-mono space-y-2">
                <div className="flex items-center space-x-1.5 font-bold">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-[#8E2F2B]" />
                  <span>Operations Access Required</span>
                </div>
                <p className="text-[11px] leading-relaxed">
                  Citizen accounts are not authorized for tactical operations or live command data. Sign in below with an Officer or Admin account, or sign out to reset your session.
                </p>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-2.5 py-1 rounded bg-[#8E2F2B] text-white text-[10px] font-bold hover:bg-[#702420] transition-colors cursor-pointer"
                >
                  Sign Out Citizen Session
                </button>
              </div>
            )}
          </div>

          {/* Operational Login Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-mono font-bold text-[#202622]">
                  Authorized Phone Number
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setPhone('9876543211');
                    setPassword('Officer@123');
                  }}
                  className="text-[10px] font-mono text-[#23483A] hover:underline font-bold"
                >
                  Fill Officer Creds
                </button>
              </div>
              <div className="relative">
                <Phone className="w-4 h-4 text-[#536A72] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="9876543211"
                  autoComplete="tel"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4F1E8] border border-[#C7B89B] rounded-xl text-xs font-mono text-[#202622] placeholder:text-[#536A72]/60 focus:outline-none focus:border-[#23483A]"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-mono font-bold text-[#202622] block mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#536A72] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Officer@123"
                  autoComplete="current-password"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4F1E8] border border-[#C7B89B] rounded-xl text-xs font-mono text-[#202622] placeholder:text-[#536A72]/60 focus:outline-none focus:border-[#23483A]"
                />
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-[#8E2F2B] text-xs font-mono">
                {error}
              </div>
            )}

            <div className="pt-1 flex items-center space-x-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-2.5 rounded-xl bg-[#23483A] text-[#FAF9F3] text-xs font-heading font-bold hover:bg-[#1b382d] transition-all cursor-pointer shadow-md disabled:opacity-50"
              >
                {loading ? 'Authenticating...' : 'Log In to Operations'}
              </button>

              {currentRole && (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-3 py-2.5 rounded-xl bg-[#F4F1E8] border border-[#C7B89B] text-[#8E2F2B] hover:bg-[#E8E6DC] text-xs font-mono font-bold transition-all cursor-pointer flex items-center space-x-1"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  </ModalPortal>
);
};

