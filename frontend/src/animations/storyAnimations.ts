import { animate, stagger } from 'animejs';
import { isReducedMotion } from './sosAnimations';

export function animateRiskExplainerSteps(elements: ArrayLike<HTMLElement> | string) {
  if (isReducedMotion()) return;

  animate(elements, {
    opacity: [0, 1],
    translateY: [24, 0],
    scale: [0.96, 1],
    delay: stagger(140, { start: 100 }),
    duration: 500,
    easing: 'easeOutQuart',
  });
}

export function animateScannerLine(element: HTMLElement | null): any {
  if (!element || isReducedMotion()) return null;

  return animate(element, {
    translateY: ['0%', '100%', '0%'],
    opacity: [0.4, 0.9, 0.4],
    duration: 3200,
    easing: 'easeInOutQuad',
    loop: true,
  });
}

export function animateStorySlideEnter(element: HTMLElement | null) {
  if (!element || isReducedMotion()) return;

  animate(element, {
    opacity: [0, 1],
    translateY: [20, 0],
    duration: 400,
    easing: 'easeOutCubic',
  });
}
