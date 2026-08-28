import React, { useEffect, useRef } from 'react';
import { attachCardHoverEffect } from '../../animations/cursorInteractions';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  interactive?: boolean;
  active?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  interactive = false,
  active = false,
  className = '',
  ...props
}) => {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (interactive && cardRef.current) {
      const cleanup = attachCardHoverEffect(cardRef.current);
      return cleanup;
    }
  }, [interactive]);

  return (
    <div
      ref={cardRef}
      className={`bg-surface border ${
        active 
          ? 'border-accent bg-main shadow-md' 
          : 'border-border/50 hover:border-border'
      } rounded-2xl p-4 sm:p-5 transition-all duration-150 ${
        interactive ? 'cursor-pointer select-none tactile-press' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
