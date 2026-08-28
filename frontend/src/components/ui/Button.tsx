import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'emergency' | 'warning' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'secondary',
  size = 'md',
  fullWidth = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-heading font-bold tracking-wide transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed tactile-press touch-target-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#23483A] rounded-xl';
  
  const sizeStyles = {
    sm: 'px-4 py-2 text-xs min-h-[44px]',
    md: 'px-5 py-3 text-sm min-h-[52px]',
    lg: 'px-6 py-4 text-base min-h-[60px]',
  };

  const variantStyles = {
    emergency: 'bg-[#8E2F2B] text-[#FAF9F3] hover:bg-[#722522] active:bg-[#581c1a] border border-[#8E2F2B] shadow-md',
    warning: 'bg-[#D88A32] text-[#FAF9F3] hover:bg-[#c27a29] active:bg-[#a6671f] border border-[#D88A32] shadow-sm',
    secondary: 'bg-[#23483A] text-[#FAF9F3] hover:bg-[#1b382d] active:bg-[#142a22] border border-[#23483A] shadow-sm',
    outline: 'bg-transparent text-[#202622] border-2 border-[#C7B89B] hover:border-[#23483A] hover:bg-[#E8E6DC]',
    ghost: 'bg-transparent text-[#536A72] hover:bg-[#E8E6DC] hover:text-[#202622]',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
