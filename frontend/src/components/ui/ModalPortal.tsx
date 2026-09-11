import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';

interface ModalPortalProps {
  children: React.ReactNode;
  onClose?: () => void;
  closeOnEscape?: boolean;
  lockScroll?: boolean;
}

let activeModalsCount = 0;
let previousBodyOverflow = '';

export const ModalPortal: React.FC<ModalPortalProps> = ({
  children,
  onClose,
  closeOnEscape = true,
  lockScroll = true,
}) => {
  // Manage body scroll lock
  useEffect(() => {
    if (typeof document === 'undefined' || !lockScroll) return;

    if (activeModalsCount === 0) {
      previousBodyOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
    }
    activeModalsCount++;

    return () => {
      if (!lockScroll) return;
      activeModalsCount = Math.max(0, activeModalsCount - 1);
      if (activeModalsCount === 0) {
        document.body.style.overflow = previousBodyOverflow;
      }
    };
  }, [lockScroll]);

  // Optional global Escape key listener
  useEffect(() => {
    if (!closeOnEscape || !onClose) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeOnEscape, onClose]);

  if (typeof document === 'undefined') {
    return null;
  }

  return createPortal(children, document.body);
};
