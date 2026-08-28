import React, { useEffect, useRef } from 'react';
import { WHY_RISK_STEPS } from '../../data/mockStoryData';
import { animateRiskExplainerSteps } from '../../animations/storyAnimations';
import { X, HelpCircle, ArrowRight, ShieldCheck } from 'lucide-react';

interface WhyRiskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowRoute: () => void;
}

export const WhyRiskModal: React.FC<WhyRiskModalProps> = ({ isOpen, onClose, onShowRoute }) => {
  const stepsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && stepsRef.current) {
      const stepCards = stepsRef.current.querySelectorAll('.risk-step-card');
      animateRiskExplainerSteps(stepCards as unknown as ArrayLike<HTMLElement>);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/60 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-surface border-2 border-border rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-hover">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-accent/10 text-accent border border-accent/20">
              <HelpCircle className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-mono font-bold text-[#D88A32] uppercase tracking-widest block">
                GEOSPATIAL RISK EXPLAINER
              </span>
              <h2 className="text-xl sm:text-2xl font-heading font-bold text-primary">
                Why Is My Area at Risk?
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-muted hover:text-primary hover:bg-hover transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 5-Step Visual Chain Grid */}
        <div ref={stepsRef} className="space-y-3">
          {WHY_RISK_STEPS.map((step) => (
            <div
              key={step.stepNumber}
              className="risk-step-card p-4 rounded-2xl bg-main border border-border/50 flex items-start space-x-4 shadow-sm"
            >
              <span className="font-heading text-lg font-bold text-muted font-mono shrink-0">
                {step.stepNumber}
              </span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-heading font-bold text-primary">
                    {step.title}
                  </h3>
                  <span className={`font-mono text-xs font-bold ${step.statusColor}`}>
                    {step.value} <span className="text-[10px] text-muted">{step.unit}</span>
                  </span>
                </div>
                <p className="text-xs text-primary/80 mt-1 font-medium leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Actions Footer */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-hover">
          <div className="flex items-center space-x-2 text-xs font-mono text-muted">
            <ShieldCheck className="w-4 h-4 text-accent" />
            <span>AI Risk Model &bull; No complex jargon</span>
          </div>

          <button
            onClick={() => {
              onClose();
              onShowRoute();
            }}
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-accent text-surface font-heading font-bold text-sm hover:bg-[#1b382d] transition-colors flex items-center justify-center space-x-2 shadow-md"
          >
            <span>Show Safe Evacuation Route</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
};
