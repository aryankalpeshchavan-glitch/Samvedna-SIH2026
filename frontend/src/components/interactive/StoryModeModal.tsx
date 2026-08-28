import React, { useState, useEffect, useRef } from 'react';
import { STORY_MODE_SLIDES } from '../../data/mockStoryData';
import { animateStorySlideEnter } from '../../animations/storyAnimations';
import { X, ChevronLeft, ChevronRight, Sparkles, ShieldCheck } from 'lucide-react';

interface StoryModeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const StoryModeModal: React.FC<StoryModeModalProps> = ({ isOpen, onClose }) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const slideRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && slideRef.current) {
      animateStorySlideEnter(slideRef.current);
    }
  }, [isOpen, currentSlideIndex]);

  if (!isOpen) return null;

  const slide = STORY_MODE_SLIDES[currentSlideIndex];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-primary/70 backdrop-blur-md">
      <div className="w-full max-w-xl bg-surface border-2 border-accent rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative overflow-hidden font-sans">
        
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-hover">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-5 h-5 text-accent" />
            <span className="font-mono text-xs font-bold text-accent uppercase tracking-widest">
              SIH26001 STORY PRESENTATION &bull; {currentSlideIndex + 1} / {STORY_MODE_SLIDES.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-muted hover:text-primary hover:bg-hover"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Story Slide Content */}
        <div ref={slideRef} className="space-y-4 py-4 min-h-[180px]">
          <span className="text-xs font-mono font-bold text-[#D88A32] tracking-wider uppercase block">
            {slide.subtitle}
          </span>
          <h2 className="text-2xl sm:text-3xl font-heading font-black text-primary leading-tight">
            {slide.title}
          </h2>
          <p className="text-sm sm:text-base text-primary/85 font-medium leading-relaxed">
            {slide.description}
          </p>
        </div>

        {/* Controls Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-hover">
          <div className="flex items-center space-x-1.5">
            {STORY_MODE_SLIDES.map((_, idx) => (
              <span
                key={idx}
                className={`h-2 rounded-full transition-all ${
                  idx === currentSlideIndex ? 'w-8 bg-accent' : 'w-2 bg-border'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center space-x-2">
            <button
              disabled={currentSlideIndex === 0}
              onClick={() => setCurrentSlideIndex((prev) => prev - 1)}
              className="p-2.5 rounded-xl border border-border disabled:opacity-30 disabled:cursor-not-allowed hover:bg-hover text-primary"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              disabled={currentSlideIndex === STORY_MODE_SLIDES.length - 1}
              onClick={() => setCurrentSlideIndex((prev) => prev + 1)}
              className="px-4 py-2.5 rounded-xl bg-accent text-surface font-heading font-bold text-xs hover:bg-[#1b382d] flex items-center space-x-1 disabled:opacity-50"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
