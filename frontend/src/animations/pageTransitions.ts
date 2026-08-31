import { animate, stagger } from 'animejs';
import { isReducedMotion } from './sosAnimations';

export function animateStaggerIn(elements: ArrayLike<HTMLElement> | string) {
  if (isReducedMotion()) return;

  animate(elements, {
    opacity: [0, 1],
    translateY: [16, 0],
    delay: stagger(60, { start: 40 }),
    duration: 350,
    easing: 'easeOutQuart',
  });
}

export function animatePageEnter(container: HTMLElement | null) {
  if (!container || isReducedMotion()) return;

  animate(container, {
    opacity: [0, 1],
    translateY: [8, 0],
    duration: 250,
    easing: 'easeOutQuad',
  });
}
