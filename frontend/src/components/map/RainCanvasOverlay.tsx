import React, { useEffect, useRef } from 'react';

interface RainCanvasOverlayProps {
  isActive: boolean;
}

export const RainCanvasOverlay: React.FC<RainCanvasOverlayProps> = ({ isActive }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!isActive || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle pool
    const particleCount = 120;
    const particles: { x: number; y: number; length: number; speed: number; opacity: number }[] = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        length: 12 + Math.random() * 16,
        speed: 8 + Math.random() * 6,
        opacity: 0.2 + Math.random() * 0.35,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = '#536A72';
      ctx.lineWidth = 1.2;
      ctx.lineCap = 'round';

      for (let i = 0; i < particleCount; i++) {
        const p = particles[i];
        ctx.beginPath();
        ctx.globalAlpha = p.opacity;
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - p.length * 0.2, p.y + p.length);
        ctx.stroke();

        p.y += p.speed;
        p.x -= p.speed * 0.2;

        if (p.y > height) {
          p.y = -p.length;
          p.x = Math.random() * width;
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
    };
  }, [isActive]);

  if (!isActive) return null;

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-20 w-full h-full"
    />
  );
};
