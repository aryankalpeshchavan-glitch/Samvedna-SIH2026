import React, { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { useTranslation } from '../../i18n/LanguageContext';
import { verifyVolunteerQrCode, VolunteerRecord } from '../../services/volunteerVerification';
import { ModalPortal } from '../ui/ModalPortal';
import { QrCode, Camera, X, CheckCircle2, AlertOctagon, ShieldCheck, RefreshCw, PhoneCall, Award } from 'lucide-react';

interface VolunteerQrScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ScanState = 'READY' | 'CAMERA_LOADING' | 'SCANNING' | 'RESULT_VALID' | 'RESULT_INVALID' | 'PERMISSION_DENIED';

export const VolunteerQrScannerModal: React.FC<VolunteerQrScannerModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const [scanState, setScanState] = useState<ScanState>('READY');
  const [manualIdInput, setManualIdInput] = useState('');
  const [verifiedVolunteer, setVerifiedVolunteer] = useState<VolunteerRecord | null>(null);
  const [scannedCodeText, setScannedCodeText] = useState<string>('');

  const html5QrcodeRef = useRef<Html5Qrcode | null>(null);
  const scannerRegionId = 'qr-reader-region-container';

  const stopCameraScan = async () => {
    if (html5QrcodeRef.current && html5QrcodeRef.current.isScanning) {
      try {
        await html5QrcodeRef.current.stop();
        html5QrcodeRef.current.clear();
      } catch (err) {
        console.warn('[QR Scanner] Error stopping camera:', err);
      }
    }
  };

  const startCameraScan = async () => {
    setScanState('CAMERA_LOADING');
    try {
      if (!html5QrcodeRef.current) {
        html5QrcodeRef.current = new Html5Qrcode(scannerRegionId);
      } else if (html5QrcodeRef.current.isScanning) {
        await stopCameraScan();
      }

      await html5QrcodeRef.current.start(
        { facingMode: 'environment' },
        {
          fps: 10,
          qrbox: { width: 220, height: 220 },
        },
        (decodedText) => {
          // Success callback on QR code detected
          handleCodeDetected(decodedText);
        },
        (_errorMessage) => {
          // Frame parse error (ignored per frame)
        }
      );
      setScanState('SCANNING');
    } catch (err) {
      console.warn('[QR Scanner] Camera error:', err);
      setScanState('PERMISSION_DENIED');
    }
  };

  const handleCodeDetected = async (code: string) => {
    await stopCameraScan();
    setScannedCodeText(code);
    const result = verifyVolunteerQrCode(code);
    if (result.isValid && result.volunteer) {
      setVerifiedVolunteer(result.volunteer);
      setScanState('RESULT_VALID');
    } else {
      setVerifiedVolunteer(null);
      setScanState('RESULT_INVALID');
    }
  };

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualIdInput.trim()) return;
    handleCodeDetected(manualIdInput);
  };

  const handleResetScan = async () => {
    await stopCameraScan();
    setVerifiedVolunteer(null);
    setScannedCodeText('');
    setManualIdInput('');
    setScanState('READY');
  };

  const handleClose = async () => {
    await stopCameraScan();
    onClose();
  };

  useEffect(() => {
    if (!isOpen) {
      stopCameraScan();
    }
    return () => {
      stopCameraScan();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <ModalPortal onClose={handleClose}>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#202622]/70 backdrop-blur-sm font-sans animate-fade-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby="qr-modal-title"
        onClick={handleClose}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-lg bg-[#FAF9F3] border-2 border-[#23483A] rounded-3xl p-6 shadow-2xl space-y-5 relative max-h-[90vh] overflow-y-auto"
        >
          
          {/* Header */}
          <div className="flex items-start justify-between pb-3 border-b border-[#C7B89B]/50">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-2xl bg-[#23483A]/10 text-[#23483A] border border-[#23483A]/30">
                <QrCode className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] font-mono font-bold text-[#23483A] uppercase tracking-widest block">
                  OFFICIAL RESPONDER VERIFICATION
                </span>
                <h2 id="qr-modal-title" className="text-lg font-heading font-black text-[#202622] uppercase tracking-wide px-2 py-0.5">
                  {t('qr.verifyTitle')}
                </h2>
              </div>
            </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-xl text-[#536A72] hover:text-[#202622] hover:bg-[#E8E6DC]"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-[#536A72] font-medium leading-relaxed">
          {t('qr.verifySubtitle')}
        </p>

        {/* 1. Camera Viewport Section */}
        {(scanState === 'READY' || scanState === 'CAMERA_LOADING' || scanState === 'SCANNING') && (
          <div className="space-y-3">
            <div className="relative w-full rounded-2xl overflow-hidden bg-[#202622] border-2 border-[#C7B89B] min-h-[240px] flex items-center justify-center">
              
              {/* HTML5 QR Code Mount Element */}
              <div id={scannerRegionId} className="w-full h-full text-white text-center" />

              {scanState === 'READY' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center text-[#FAF9F3] bg-[#202622]/90 space-y-3">
                  <Camera className="w-10 h-10 text-[#FAF9F3]/60 animate-pulse" />
                  <p className="text-xs font-mono text-[#FAF9F3]/80">
                    Camera inactive. Click below to start scanner.
                  </p>
                  <button
                    onClick={startCameraScan}
                    className="px-5 py-2.5 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] transition-colors flex items-center space-x-2 cursor-pointer shadow-md"
                  >
                    <Camera className="w-4 h-4" />
                    <span>{t('qr.startCamera')}</span>
                  </button>
                </div>
              )}

              {scanState === 'CAMERA_LOADING' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center text-[#FAF9F3] bg-[#202622]/90 space-y-2">
                  <RefreshCw className="w-8 h-8 text-[#D88A32] animate-spin" />
                  <span className="text-xs font-mono">Initializing camera feed...</span>
                </div>
              )}

              {scanState === 'SCANNING' && (
                <div className="absolute inset-x-0 top-2 px-3 py-1 bg-black/60 backdrop-blur-md text-white text-[11px] font-mono flex items-center justify-between z-10">
                  <span className="flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#23483A] animate-ping" />
                    <span>{t('qr.scanning')}</span>
                  </span>
                  <button
                    onClick={stopCameraScan}
                    className="px-2 py-0.5 rounded bg-white/20 hover:bg-white/30 text-[10px] font-bold"
                  >
                    {t('qr.stopCamera')}
                  </button>
                </div>
              )}
            </div>

            {/* Quick Demo Test Action Pills for Hackathon Judges */}
            <div className="p-3 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/50 space-y-2">
              <span className="text-[10px] font-mono font-bold text-[#536A72] uppercase tracking-wider block">
                Hackathon Demo Quick Testing:
              </span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleCodeDetected('NDRF-VOL-7842')}
                  className="px-3 py-2 rounded-xl bg-[#23483A]/10 border border-[#23483A]/30 text-[#23483A] text-xs font-heading font-bold hover:bg-[#23483A] hover:text-[#FAF9F3] transition-colors text-left flex items-center space-x-1.5 cursor-pointer"
                >
                  <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{t('qr.demoValid')}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleCodeDetected('FAKE-BADGE-999')}
                  className="px-3 py-2 rounded-xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/30 text-[#8E2F2B] text-xs font-heading font-bold hover:bg-[#8E2F2B] hover:text-[#FAF9F3] transition-colors text-left flex items-center space-x-1.5 cursor-pointer"
                >
                  <AlertOctagon className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate">{t('qr.demoInvalid')}</span>
                </button>
              </div>
            </div>

            {/* Manual Code Input Form */}
            <form onSubmit={handleManualSubmit} className="pt-1 flex items-center space-x-2">
              <input
                type="text"
                value={manualIdInput}
                onChange={(e) => setManualIdInput(e.target.value)}
                placeholder="e.g. NDRF-VOL-7842"
                className="flex-1 px-3.5 py-2 rounded-xl bg-white border border-[#C7B89B] text-xs font-mono text-[#202622] uppercase placeholder-[#536A72]/50 focus:outline-none focus:border-[#23483A]"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] transition-colors cursor-pointer shrink-0"
              >
                {t('qr.verifyButton')}
              </button>
            </form>
          </div>
        )}

        {/* 2. State: Camera Permission Denied Fallback */}
        {scanState === 'PERMISSION_DENIED' && (
          <div className="p-4 rounded-2xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 space-y-3">
            <div className="flex items-center space-x-2 text-[#8E2F2B]">
              <AlertOctagon className="w-5 h-5" />
              <h3 className="text-sm font-heading font-bold">{t('qr.permDenied')}</h3>
            </div>
            <p className="text-xs text-[#202622]/80">
              Camera access is disabled or unavailable on this device. You can verify volunteer credentials manually below:
            </p>
            <form onSubmit={handleManualSubmit} className="flex items-center space-x-2 pt-1">
              <input
                type="text"
                value={manualIdInput}
                onChange={(e) => setManualIdInput(e.target.value)}
                placeholder="e.g. NDRF-VOL-7842"
                className="flex-1 px-3.5 py-2 rounded-xl bg-white border border-[#C7B89B] text-xs font-mono uppercase text-[#202622]"
              />
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs"
              >
                {t('qr.verifyButton')}
              </button>
            </form>
          </div>
        )}

        {/* 3. State: Valid Verified Responder Result */}
        {scanState === 'RESULT_VALID' && verifiedVolunteer && (
          <div className="p-5 rounded-2xl bg-[#23483A]/10 border-2 border-[#23483A] space-y-4 shadow-md font-sans">
            <div className="flex items-center justify-between pb-3 border-b border-[#23483A]/20">
              <div className="flex items-center space-x-2 text-[#23483A]">
                <CheckCircle2 className="w-6 h-6 shrink-0" />
                <span className="text-xs font-heading font-black tracking-wider uppercase">
                  {t('qr.validBadge')}
                </span>
              </div>
              <span className="px-2.5 py-1 rounded-md bg-[#23483A] text-[#FAF9F3] text-[10px] font-mono font-black uppercase">
                {verifiedVolunteer.status}
              </span>
            </div>

            <div className="space-y-2">
              <div>
                <h3 className="text-xl font-heading font-black text-[#202622]">
                  {verifiedVolunteer.name}
                </h3>
                <span className="text-xs font-mono text-[#536A72] block">
                  {verifiedVolunteer.organization}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono pt-2">
                <div className="p-2.5 rounded-xl bg-white border border-[#C7B89B]/50">
                  <span className="text-[10px] text-[#536A72] block">ROLE</span>
                  <strong className="text-[#202622]">{verifiedVolunteer.role}</strong>
                </div>

                <div className="p-2.5 rounded-xl bg-white border border-[#C7B89B]/50">
                  <span className="text-[10px] text-[#536A72] block">BADGE ID</span>
                  <strong className="text-[#23483A]">{verifiedVolunteer.id}</strong>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-white border border-[#C7B89B]/50 text-xs font-mono space-y-1">
                <div className="flex items-center space-x-1.5 text-[#A87C58]">
                  <Award className="w-4 h-4" />
                  <span className="font-bold text-[#202622]">{verifiedVolunteer.certifications}</span>
                </div>
                <div className="flex items-center space-x-1.5 text-[#23483A] pt-1">
                  <PhoneCall className="w-4 h-4" />
                  <a href={`tel:${verifiedVolunteer.phone}`} className="font-bold hover:underline">
                    {verifiedVolunteer.phone}
                  </a>
                </div>
              </div>
            </div>

            <button
              onClick={handleResetScan}
              className="w-full py-2.5 px-4 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-[#1b382d] transition-colors cursor-pointer"
            >
              {t('qr.scanAnother')}
            </button>
          </div>
        )}

        {/* 4. State: Invalid / Unrecognized QR Code Result */}
        {scanState === 'RESULT_INVALID' && (
          <div className="p-5 rounded-2xl bg-[#8E2F2B]/10 border-2 border-[#8E2F2B] space-y-4 shadow-md font-sans">
            <div className="flex items-center space-x-2 text-[#8E2F2B] pb-2 border-b border-[#8E2F2B]/20">
              <AlertOctagon className="w-6 h-6 shrink-0" />
              <h3 className="text-sm font-heading font-black uppercase tracking-wide">
                {t('qr.invalidBadge')}
              </h3>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <p className="text-[#202622] leading-relaxed font-medium">
                {t('qr.invalidDesc')}
              </p>
              <div className="p-2.5 rounded-xl bg-white border border-[#8E2F2B]/30">
                <span className="text-[10px] text-[#536A72] block">SCANNED PAYLOAD</span>
                <code className="text-[#8E2F2B] font-bold break-all">{scannedCodeText}</code>
              </div>
            </div>

            <button
              onClick={handleResetScan}
              className="w-full py-2.5 px-4 rounded-xl bg-[#202622] text-[#FAF9F3] font-heading font-bold text-xs hover:bg-black transition-colors cursor-pointer"
            >
              {t('qr.scanAnother')}
            </button>
          </div>
        )}

        </div>
      </div>
    </ModalPortal>
  );
};
