import React, { useEffect, useRef } from 'react';
import { Renderer, Program, Mesh, Triangle, Color } from 'ogl';

export interface SpecularHeadingProps {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'div';
  children: React.ReactNode;
  className?: string;
  radius?: number;
  lineColor?: string;
  intensity?: number;
  shineSize?: number;
  shineFade?: number;
  thickness?: number;
  speed?: number;
  followMouse?: boolean;
  proximity?: number;
  autoAnimate?: boolean;
}

const vertexShader = /* glsl */ `
  attribute vec2 position;
  attribute vec2 uv;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position, 0.0, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;
  uniform vec2 uResolution;
  uniform vec2 uMouse;
  uniform float uTime;
  uniform float uRadius;
  uniform float uThickness;
  uniform vec3 uLineColor;
  uniform float uIntensity;
  uniform float uShineSize;
  uniform float uShineFade;
  uniform float uSpeed;
  uniform float uFollowMouse;
  uniform float uProximity;
  uniform float uAutoAnimate;
  varying vec2 vUv;

  float sdRoundedBox(vec2 p, vec2 b, vec4 r) {
    r.xy = (p.x > 0.0) ? r.xy : r.zw;
    r.x  = (p.y > 0.0) ? r.x  : r.y;
    vec2 q = abs(p) - b + r.x;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r.x;
  }

  void main() {
    vec2 st = (vUv - 0.5) * uResolution;
    vec2 halfSize = uResolution * 0.5;

    float dist = sdRoundedBox(st, halfSize - vec2(uThickness * 0.5), vec4(uRadius));
    float borderMask = smoothstep(uThickness, 0.0, abs(dist));

    if (borderMask <= 0.001) {
      discard;
    }

    float angle = atan(st.y, st.x);
    vec2 mouseSt = (uMouse - 0.5) * uResolution;
    float mouseAngle = atan(mouseSt.y, mouseSt.x);

    float targetAngle = uTime * uSpeed;
    if (uFollowMouse > 0.5) {
      targetAngle = mouseAngle;
    }

    float angleDiff = abs(mod(angle - targetAngle + 3.14159265, 6.2831853) - 3.14159265);
    float shine = smoothstep(uShineSize, 0.0, angleDiff);
    shine = pow(max(shine, 0.001), uShineFade) * uIntensity;

    float proxFactor = 1.0;
    if (uFollowMouse > 0.5) {
      float mouseDist = length(st - mouseSt);
      proxFactor = smoothstep(uProximity, 0.0, mouseDist);
    }

    float finalAlpha = borderMask * shine * proxFactor;
    if (finalAlpha <= 0.001) {
      discard;
    }
    gl_FragColor = vec4(uLineColor * finalAlpha, finalAlpha);
  }
`;

export const SpecularHeading: React.FC<SpecularHeadingProps> = ({
  as: Component = 'h2',
  children,
  className = '',
  radius = 16,
  lineColor = '#23483A',
  intensity = 1.2,
  shineSize = 1.2,
  shineFade = 2.5,
  thickness = 2.0,
  speed = 1.5,
  followMouse = true,
  proximity = 200,
  autoAnimate = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    // Respect prefers-reduced-motion
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const effectiveSpeed = reducedMotion ? 0.2 : speed;

    let renderer: Renderer | null = null;
    try {
      renderer = new Renderer({
        canvas,
        alpha: true,
        dpr: Math.min(window.devicePixelRatio || 1, 2),
        premultipliedAlpha: true,
      });
      renderer.gl.clearColor(0, 0, 0, 0);

      // Immediately synchronize WebGL buffer size with CSS container dimensions on mount
      const initialWidth = container.clientWidth;
      const initialHeight = container.clientHeight;
      if (initialWidth > 0 && initialHeight > 0) {
        renderer.setSize(initialWidth, initialHeight);
      }
    } catch {
      // Graceful fallback if WebGL is unsupported
      return;
    }

    const gl = renderer.gl;
    const geometry = new Triangle(gl);
    const colorObj = new Color(lineColor);

    const program = new Program(gl, {
      vertex: vertexShader,
      fragment: fragmentShader,
      uniforms: {
        uResolution: { value: [container.clientWidth, container.clientHeight] },
        uMouse: { value: [0.5, 0.5] },
        uTime: { value: 0 },
        uRadius: { value: radius },
        uThickness: { value: thickness },
        uLineColor: { value: [colorObj.r, colorObj.g, colorObj.b] },
        uIntensity: { value: intensity },
        uShineSize: { value: shineSize },
        uShineFade: { value: shineFade },
        uSpeed: { value: effectiveSpeed },
        uFollowMouse: { value: followMouse ? 1.0 : 0.0 },
        uProximity: { value: proximity },
        uAutoAnimate: { value: autoAnimate ? 1.0 : 0.0 },
      },
      transparent: true,
      depthTest: false,
    });

    const mesh = new Mesh(gl, { geometry, program });

    let animationFrameId: number;
    let startTime = performance.now();

    const render = (now: number) => {
      const elapsed = (now - startTime) * 0.001;
      program.uniforms.uTime.value = elapsed;
      renderer?.render({ scene: mesh });
      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    const handlePointerMove = (e: PointerEvent) => {
      if (!followMouse) return;
      const rect = container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width;
      const y = 1.0 - (e.clientY - rect.top) / rect.height; // WebGL Y is inverted
      program.uniforms.uMouse.value = [x, y];
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });

    const resizeObserver = new ResizeObserver(() => {
      if (!container || !renderer) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width > 0 && height > 0) {
        renderer.setSize(width, height);
        program.uniforms.uResolution.value = [width, height];
      }
    });

    resizeObserver.observe(container);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('pointermove', handlePointerMove);
      resizeObserver.disconnect();
      if (renderer && renderer.gl) {
        const ext = renderer.gl.getExtension('WEBGL_lose_context');
        if (ext) ext.loseContext();
      }
    };
  }, [
    radius,
    lineColor,
    intensity,
    shineSize,
    shineFade,
    thickness,
    speed,
    followMouse,
    proximity,
    autoAnimate,
  ]);

  return (
    <div ref={containerRef} className="relative inline-flex items-center group max-w-full overflow-hidden rounded-2xl">
      {/* WebGL Specular Canvas Overlay (Pointer-events: none, Block display prevents descender baseline gaps) */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 block pointer-events-none w-full h-full rounded-2xl z-10"
        style={{ pointerEvents: 'none', display: 'block' }}
      />

      {/* Semantic Heading Element */}
      <Component className={`relative z-20 ${className}`}>
        {children}
      </Component>
    </div>
  );
};
