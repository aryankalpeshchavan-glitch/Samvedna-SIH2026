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
      className={`bg-[#FAF9F3] border ${
        active 
          ? 'border-[#23483A] bg-[#F4F1E8] shadow-md' 
          : 'border-[#C7B89B]/50 hover:border-[#A87C58]'
      } rounded-2xl p-4 sm:p-5 transition-all duration-150 ${
        interactive ? 'cursor-pointer select-none tactile-press' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
