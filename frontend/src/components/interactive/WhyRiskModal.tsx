import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useTranslation } from '../../i18n/LanguageContext';
import { AudioAlertButton } from '../ui/AudioAlertButton';
import {
  X,
  HelpCircle,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Sliders,
  TrendingUp,
  Activity,
  Lock,
} from 'lucide-react';
import { getIntelligenceDecision, simulateWhatIf } from '../../services/api';
import { DecisionResponse, WhatIfResponse, classifyRiskLevel } from '../../types/api';

interface WhyRiskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowRoute: () => void;
  lat?: number | null;
  lng?: number | null;
  zoneId?: string | null;
  locationName?: string | null;
}

export const WhyRiskModal: React.FC<WhyRiskModalProps> = ({
  isOpen,
  onClose,
  onShowRoute,
  lat,
  lng,
  zoneId,
  locationName,
}) => {
  const { t } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);

  // View Mode: 'decision' (Why Risk Analysis) vs 'whatif' (Scenario Simulator)
  const [activeTab, setActiveTab] = useState<'decision' | 'whatif'>('decision');

  // Decision State
  const [decision, setDecision] = useState<DecisionResponse | null>(null);
  const [isDecisionLoading, setIsDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);

  // What-If State
  const [scenarioRainfall, setScenarioRainfall] = useState<number>(100);
  const [whatIfData, setWhatIfData] = useState<WhatIfResponse | null>(null);
  const [isWhatIfLoading, setIsWhatIfLoading] = useState(false);
  const [whatIfError, setWhatIfError] = useState<string | null>(null);
  const [isWhatIfForbidden, setIsWhatIfForbidden] = useState(false);

  const effectiveLat = lat ?? 26.1445;
  const effectiveLng = lng ?? 91.7362;

  // Fetch Real Decision from Backend on modal open
  const fetchDecision = useCallback(() => {
    setIsDecisionLoading(true);
    setDecisionError(null);
    getIntelligenceDecision({
      lat: effectiveLat,
      lng: effectiveLng,
      zone_id: zoneId || undefined,
    })
      .then((data) => {
        setDecision(data);
      })
      .catch((err: any) => {
        console.error('[WhyRiskModal] Decision API failed:', err);
        setDecisionError(err?.message || 'Failed to retrieve decision intelligence');
        setDecision(null);
      })
      .finally(() => {
        setIsDecisionLoading(false);
      });
  }, [effectiveLat, effectiveLng, zoneId]);

  // Run What-If Simulation
  const runWhatIf = useCallback(async (rainfallMm: number) => {
    setIsWhatIfLoading(true);
    setWhatIfError(null);
    setIsWhatIfForbidden(false);
    try {
      const res = await simulateWhatIf({
        lat: effectiveLat,
        lng: effectiveLng,
        scenario_rainfall_mm: rainfallMm,
        zone_id: zoneId || undefined,
      });
      setWhatIfData(res);
    } catch (err: any) {
      console.error('[WhyRiskModal] WhatIf API failed:', err);
      const msg = err?.message || 'Simulation request failed';
      if (msg.includes('403') || msg.toLowerCase().includes('role') || msg.toLowerCase().includes('denied')) {
        setIsWhatIfForbidden(true);
        setWhatIfError("Role 'citizen' is restricted from running What-If scenarios. Officer or Admin credentials required by RBAC.");
      } else if (msg.includes('401')) {
        setWhatIfError('Authentication token expired or invalid. Please re-login.');
      } else {
        setWhatIfError(msg);
      }
      setWhatIfData(null);
    } finally {
      setIsWhatIfLoading(false);
    }
  }, [effectiveLat, effectiveLng, zoneId]);

  // Load decision on open
  useEffect(() => {
    if (isOpen) {
      fetchDecision();
    }
  }, [isOpen, fetchDecision]);

  if (!isOpen) return null;

  // Construct dynamic audio text
  const explainerAudioSummary = decision
    ? `Geospatial risk analysis for ${locationName || 'this location'}. Risk is ${decision.risk.risk_level} at ${(decision.risk.risk_score * 100).toFixed(0)} percent with ${(decision.risk.confidence * 100).toFixed(0)} percent confidence. Priority score is ${decision.priority.priority_score.toFixed(1)}, level ${decision.priority.priority_level}. ${decision.explanation.length} primary risk drivers identified: ${decision.explanation.map((e) => e.label).join(', ')}.`
    : t('home.whyRisk');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-[#202622]/60 backdrop-blur-sm font-sans animate-in fade-in duration-200">
      <div
        ref={modalRef}
        className="w-full max-w-2xl bg-[#FAF9F3] border-2 border-[#C7B89B] rounded-3xl p-5 sm:p-7 shadow-2xl space-y-5 max-h-[92vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[#E8E6DC]">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-[#23483A]/10 text-[#23483A] border border-[#23483A]/20 shrink-0">
              <HelpCircle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono font-bold text-[#D88A32] uppercase tracking-widest block">
                  GEOSPATIAL DECISION INTELLIGENCE
                </span>
                {decision?.data_status && (
                  <span className={`px-1.5 py-0.2 text-[9px] font-mono font-bold rounded uppercase ${
                    decision.data_status === 'live'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : 'bg-amber-100 text-amber-800 border border-amber-300'
                  }`}>
                    {decision.data_status}
                  </span>
                )}
              </div>
              <h2 className="text-xl sm:text-2xl font-heading font-black text-[#202622]">
                {locationName || t('home.whyRisk')}
              </h2>
              <span className="text-[11px] font-mono text-[#536A72]">
                Coords: {effectiveLat.toFixed(4)}° N, {effectiveLng.toFixed(4)}° E
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#536A72] hover:text-[#202622] hover:bg-[#E8E6DC] transition-colors cursor-pointer"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation: Decision vs What-If Simulator */}
        <div className="flex items-center p-1 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/50 gap-1 text-xs font-mono font-bold">
          <button
            onClick={() => setActiveTab('decision')}
            className={`flex-1 py-2 px-3 rounded-lg flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'decision'
                ? 'bg-[#23483A] text-[#FAF9F3] shadow-sm'
                : 'text-[#536A72] hover:text-[#202622]'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Risk Drivers & Priority</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('whatif');
              if (!whatIfData && !isWhatIfLoading && !whatIfError) {
                runWhatIf(scenarioRainfall);
              }
            }}
            className={`flex-1 py-2 px-3 rounded-lg flex items-center justify-center space-x-2 transition-all cursor-pointer ${
              activeTab === 'whatif'
                ? 'bg-[#23483A] text-[#FAF9F3] shadow-sm'
                : 'text-[#536A72] hover:text-[#202622]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>What-If Simulator</span>
          </button>
        </div>

        {/* ======================================================== */}
        {/* TAB 1: WHY RISK / DECISION INTELLIGENCE                  */}
        {/* ======================================================== */}
        {activeTab === 'decision' && (
          <div className="space-y-4">
            {/* Loading State */}
            {isDecisionLoading && (
              <div className="p-8 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/40 flex flex-col items-center justify-center text-center space-y-2">
                <Loader2 className="w-6 h-6 text-[#D88A32] animate-spin" />
                <span className="text-xs font-mono font-bold text-[#202622]">
                  Querying Live ML Intelligence Engine (/intelligence/decision)...
                </span>
                <span className="text-[11px] font-mono text-[#536A72]">
                  Computing Risk &rarr; Explanation &rarr; Priority &rarr; Actions
                </span>
              </div>
            )}

            {/* Error State */}
            {!isDecisionLoading && decisionError && (
              <div className="p-5 rounded-2xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-[#8E2F2B] space-y-3">
                <div className="flex items-center space-x-2 font-heading font-bold text-sm">
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <span>Intelligence Service Error</span>
                </div>
                <p className="text-xs font-mono leading-relaxed">{decisionError}</p>
                <button
                  onClick={fetchDecision}
                  className="px-3 py-1.5 rounded-lg bg-[#8E2F2B] text-white text-xs font-mono font-bold flex items-center space-x-1.5 hover:bg-[#6b2320] transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Request</span>
                </button>
              </div>
            )}

            {/* Success State */}
            {!isDecisionLoading && !decisionError && decision && (
              <div className="space-y-4">
                {/* Audio Alert Button */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/50 text-xs font-mono">
                  <span className="text-[#202622]">Audio summary for field responder:</span>
                  <AudioAlertButton text={explainerAudioSummary} size="sm" />
                </div>

                {/* KPI Metrics Dashboard Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
                    <span className="text-[10px] text-[#536A72] font-mono uppercase block">ML Risk Score</span>
                    <strong className={`text-base font-heading font-black ${
                      classifyRiskLevel(decision.risk.risk_score) === 'HIGH'
                        ? 'text-[#C6533C]'
                        : classifyRiskLevel(decision.risk.risk_score) === 'MEDIUM'
                        ? 'text-[#D88A32]'
                        : 'text-[#23483A]'
                    }`}>
                      {(decision.risk.risk_score * 100).toFixed(1)}%
                    </strong>
                    <span className="text-[9px] font-mono text-[#536A72] block">
                      Level: {decision.risk.risk_level}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
                    <span className="text-[10px] text-[#536A72] font-mono uppercase block">Confidence</span>
                    <strong className="text-base font-heading font-black text-[#23483A]">
                      {(decision.risk.confidence * 100).toFixed(1)}%
                    </strong>
                    <span className="text-[9px] font-mono text-[#536A72] block">Calibrated XGB</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
                    <span className="text-[10px] text-[#536A72] font-mono uppercase block">Priority Score</span>
                    <strong className="text-base font-heading font-black text-[#D88A32]">
                      {decision.priority.priority_score.toFixed(1)}
                    </strong>
                    <span className="text-[9px] font-mono text-[#536A72] block">
                      Level: {decision.priority.priority_level}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-[#F4F1E8] border border-[#C7B89B]/40">
                    <span className="text-[10px] text-[#536A72] font-mono uppercase block">Data Status</span>
                    <strong className="text-base font-heading font-black text-[#202622] uppercase text-xs">
                      {decision.data_status}
                    </strong>
                    <span className="text-[9px] font-mono text-[#536A72] block">
                      {new Date(decision.computed_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                {/* Variable Explanation Driver Cards */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-bold text-[#536A72] uppercase tracking-wider block">
                      Primary Risk Drivers ({decision.explanation.length})
                    </span>
                    <span className="text-[10px] font-mono text-[#536A72]">
                      SHAP &amp; Environmental Attribution
                    </span>
                  </div>

                  {decision.explanation.length === 0 ? (
                    <div className="p-4 rounded-xl bg-[#F4F1E8] text-xs font-mono text-[#536A72] text-center">
                      No elevated hazard drivers detected at this location.
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      {decision.explanation.map((item, index) => {
                        const stepNum = String(index + 1).padStart(2, '0');
                        return (
                          <div
                            key={item.key || index}
                            className="risk-step-card p-3.5 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/50 flex items-start space-x-3.5 shadow-sm"
                          >
                            <span className="font-heading text-sm font-bold text-[#536A72] font-mono shrink-0 pt-0.5">
                              {stepNum}
                            </span>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-2">
                                <h3 className="text-xs font-heading font-bold text-[#202622] truncate">
                                  {item.label}
                                </h3>
                                <div className="flex items-center space-x-2 shrink-0">
                                  {item.category && (
                                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-[#23483A]/10 text-[#23483A] font-bold">
                                      {item.category}
                                    </span>
                                  )}
                                  {item.value !== null && item.value !== undefined && (
                                    <span className="font-mono text-xs font-bold text-[#D88A32]">
                                      {item.value > 1 ? item.value.toFixed(1) : (item.value * 100).toFixed(1) + '%'}
                                      {item.unit && <span className="text-[10px] text-[#536A72] ml-0.5">{item.unit}</span>}
                                    </span>
                                  )}
                                </div>
                              </div>
                              <p className="text-xs text-[#202622]/80 mt-1 font-medium leading-relaxed">
                                {item.description}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Recommended Response Actions */}
                {decision.actions && decision.actions.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#23483A]/5 border border-[#23483A]/20 space-y-2">
                    <span className="text-xs font-mono font-bold text-[#23483A] uppercase tracking-wider block">
                      Recommended Operational Actions ({decision.actions.length})
                    </span>
                    <ul className="space-y-1.5 text-xs text-[#202622] font-medium">
                      {decision.actions.map((act, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-[#23483A] font-bold shrink-0">&bull;</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* TAB 2: WHAT-IF SCENARIO SIMULATOR                        */}
        {/* ======================================================== */}
        {activeTab === 'whatif' && (
          <div className="space-y-4">
            {/* Simulation Notice Banner (Mandatory Notice) */}
            <div className="p-3.5 rounded-2xl bg-[#D88A32]/15 border-2 border-[#D88A32] text-[#202622] space-y-1 shadow-sm">
              <div className="flex items-center space-x-2 font-mono font-black text-xs text-[#D88A32] tracking-wider uppercase">
                <TrendingUp className="w-4 h-4 text-[#D88A32]" />
                <span>SIMULATION — NOT A FORECAST</span>
              </div>
              <p className="text-xs font-medium leading-relaxed text-[#202622]/90">
                This scenario simulator models theoretical risk escalation under projected rainfall anomalies. It does not replace active real-time telemetry.
              </p>
            </div>

            {/* Scenario Parameter Controls */}
            <div className="p-4 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/50 space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono font-bold text-[#536A72] uppercase">
                  Additional Rainfall Scenario (+mm)
                </label>
                <span className="font-mono text-sm font-bold text-[#23483A]">
                  +{scenarioRainfall} mm
                </span>
              </div>

              {/* Slider */}
              <input
                type="range"
                min="10"
                max="300"
                step="10"
                value={scenarioRainfall}
                onChange={(e) => setScenarioRainfall(Number(e.target.value))}
                className="w-full accent-[#23483A] cursor-pointer"
              />

              {/* Preset Buttons */}
              <div className="flex items-center gap-2">
                {[25, 50, 100, 200].map((val) => (
                  <button
                    key={val}
                    onClick={() => {
                      setScenarioRainfall(val);
                      runWhatIf(val);
                    }}
                    className={`flex-1 py-1.5 rounded-lg text-xs font-mono font-bold border transition-colors cursor-pointer ${
                      scenarioRainfall === val
                        ? 'bg-[#23483A] text-white border-[#23483A]'
                        : 'bg-[#FAF9F3] text-[#202622] border-[#C7B89B]/60 hover:bg-[#E8E6DC]'
                    }`}
                  >
                    +{val}mm
                  </button>
                ))}
              </div>

              <button
                onClick={() => runWhatIf(scenarioRainfall)}
                disabled={isWhatIfLoading}
                className="w-full py-2.5 rounded-xl bg-[#23483A] text-white text-xs font-mono font-bold flex items-center justify-center space-x-2 hover:bg-[#1b382d] transition-colors cursor-pointer disabled:opacity-50"
              >
                {isWhatIfLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Simulating Scenario Impact...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Run Simulation (+{scenarioRainfall}mm)</span>
                  </>
                )}
              </button>
            </div>

            {/* RBAC 403 Forbidden Error State */}
            {isWhatIfForbidden && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 space-y-2">
                <div className="flex items-center space-x-2 font-heading font-bold text-xs">
                  <Lock className="w-4 h-4 text-amber-700" />
                  <span>Officer / Admin Authorization Required</span>
                </div>
                <p className="text-xs font-mono leading-relaxed">
                  The What-If scenario simulator is restricted to disaster management officers and emergency coordinators. Citizen accounts do not have permission to execute what-if projections.
                </p>
              </div>
            )}

            {/* General Error State */}
            {!isWhatIfForbidden && whatIfError && (
              <div className="p-4 rounded-2xl bg-[#8E2F2B]/10 border border-[#8E2F2B]/40 text-[#8E2F2B] text-xs font-mono space-y-1">
                <span className="font-bold block">Simulation Error:</span>
                <p>{whatIfError}</p>
              </div>
            )}

            {/* What-If Simulation Results */}
            {!isWhatIfLoading && whatIfData && (
              <div className="space-y-3 animate-in fade-in duration-200">
                {/* Comparison Grid */}
                <div className="grid grid-cols-2 gap-3">
                  {/* Current State */}
                  <div className="p-3.5 rounded-2xl bg-[#F4F1E8] border border-[#C7B89B]/40 space-y-1">
                    <span className="text-[10px] font-mono text-[#536A72] uppercase font-bold block">
                      Current Baseline
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <strong className="text-lg font-heading font-black text-[#202622]">
                        {(whatIfData.current_risk_score * 100).toFixed(1)}%
                      </strong>
                      <span className="text-[11px] font-mono text-[#536A72]">
                        {whatIfData.current_priority_level}
                      </span>
                    </div>
                  </div>

                  {/* Projected State */}
                  <div className="p-3.5 rounded-2xl bg-[#D88A32]/10 border-2 border-[#D88A32]/60 space-y-1">
                    <span className="text-[10px] font-mono text-[#D88A32] uppercase font-bold block">
                      Projected (+{scenarioRainfall}mm)
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <strong className="text-lg font-heading font-black text-[#C6533C]">
                        {(whatIfData.projected_risk_score * 100).toFixed(1)}%
                      </strong>
                      <span className="text-[11px] font-mono font-bold text-[#D88A32]">
                        {whatIfData.projected_priority_level}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Projected Escalation Actions */}
                {whatIfData.projected_actions && whatIfData.projected_actions.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#FAF9F3] border border-[#C7B89B]/60 space-y-2">
                    <span className="text-xs font-mono font-bold text-[#C6533C] uppercase tracking-wider block">
                      Simulated Operational Escalations ({whatIfData.projected_actions.length})
                    </span>
                    <ul className="space-y-1.5 text-xs text-[#202622] font-medium">
                      {whatIfData.projected_actions.map((act, i) => (
                        <li key={i} className="flex items-start space-x-2">
                          <span className="text-[#C6533C] font-bold shrink-0">&rarr;</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Actions Footer */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-[#E8E6DC]">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#536A72]">
            <ShieldCheck className="w-4 h-4 text-[#23483A]" />
            <span>CrisisCore XGBoost Intelligence &bull; Live Grounding</span>
          </div>

          <button
            onClick={() => {
              onClose();
              onShowRoute();
            }}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[#23483A] text-[#FAF9F3] font-heading font-bold text-sm hover:bg-[#1b382d] transition-colors flex items-center justify-center space-x-2 shadow-md cursor-pointer"
          >
            <span>{t('home.showSafeRoute')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
