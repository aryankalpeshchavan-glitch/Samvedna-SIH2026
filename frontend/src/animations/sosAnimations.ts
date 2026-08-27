import { animate } from 'animejs';

export function isReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function animateSosPulse(element: HTMLElement | null): any {
  if (!element || isReducedMotion()) return null;

  return animate(element, {
    scale: [1, 1.05, 1],
    boxShadow: [
      '0 0 20px rgba(239, 68, 68, 0.4)',
      '0 0 45px rgba(239, 68, 68, 0.85)',
      '0 0 20px rgba(239, 68, 68, 0.4)',
    ],
    duration: 2200,
    easing: 'easeInOutQuad',
    loop: true,
  });
}

export function animateSosPress(element: HTMLElement | null, onComplete?: () => void) {
  if (!element) {
    onComplete?.();
    return;
  }

  if (isReducedMotion()) {
    onComplete?.();
    return;
  }

  animate(element, {
    scale: [1, 0.92, 1.02, 1],
    duration: 350,
    easing: 'easeOutElastic(1, .6)',
    onComplete: () => {
      onComplete?.();
    },
  });
}

export function animateModalEntrance(element: HTMLElement | null) {
  if (!element || isReducedMotion()) return;

  animate(element, {
    opacity: [0, 1],
    scale: [0.94, 1],
    translateY: [20, 0],
    duration: 300,
    easing: 'easeOutCubic',
  });
}

export function animateSendingRing(element: HTMLElement | null) {
  if (!element || isReducedMotion()) return;

  return animate(element, {
    rotate: '1turn',
    duration: 1800,
    easing: 'linear',
    loop: true,
  });
}
