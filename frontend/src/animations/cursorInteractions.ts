import { animate } from 'animejs';
import { isReducedMotion } from './sosAnimations';

export function attachCardHoverEffect(element: HTMLElement | null): () => void {
  if (!element || isReducedMotion()) return () => {};
  if (typeof window !== 'undefined' && window.matchMedia('(pointer: coarse)').matches) {
    // Disable hover effects on touch screens
    return () => {};
  }

  const handleMouseEnter = () => {
    animate(element, {
      translateY: -3,
      scale: 1.01,
      duration: 200,
      easing: 'easeOutCubic',
    });
  };

  const handleMouseLeave = () => {
    animate(element, {
      translateY: 0,
      scale: 1,
      duration: 250,
      easing: 'easeOutCubic',
    });
  };

  element.addEventListener('mouseenter', handleMouseEnter);
  element.addEventListener('mouseleave', handleMouseLeave);

  return () => {
    element.removeEventListener('mouseenter', handleMouseEnter);
    element.removeEventListener('mouseleave', handleMouseLeave);
  };
}
