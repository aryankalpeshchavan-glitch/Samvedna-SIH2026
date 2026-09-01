import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import { EPICENTER } from '../../utils/constants';

// Generate a risk heatmap as a canvas image
function generateHeatmapCanvas(width = 512, height = 512) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');

  // Epicenter in normalized canvas coords (center-ish)
  const cx = width * 0.5;
  const cy = height * 0.45;

  // Create multiple radial gradient layers for realistic heatmap
  const gradients = [
    { x: cx, y: cy, r: 140, intensity: 1.0 },
    { x: cx - 30, y: cy + 20, r: 100, intensity: 0.8 },
    { x: cx + 50, y: cy - 10, r: 80, intensity: 0.7 },
    { x: cx - 20, y: cy + 60, r: 120, intensity: 0.6 },
    { x: cx + 30, y: cy + 80, r: 90, intensity: 0.5 },
  ];

  // Background transparent
  ctx.clearRect(0, 0, width, height);

  gradients.forEach(({ x, y, r, intensity }) => {
    const grad = ctx.createRadialGradient(x, y, 0, x, y, r);
    grad.addColorStop(0, `rgba(255, 26, 26, ${0.6 * intensity})`);
    grad.addColorStop(0.3, `rgba(255, 140, 0, ${0.45 * intensity})`);
    grad.addColorStop(0.6, `rgba(255, 215, 0, ${0.3 * intensity})`);
    grad.addColorStop(0.85, `rgba(45, 138, 45, ${0.15 * intensity})`);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);
  });

  return canvas;
}

export default function RiskHeatmap({ viewer }) {
  const layerRef = useRef(null);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    let cancelled = false;

    async function addHeatmap() {
      const canvas = generateHeatmapCanvas();
      const dataUrl = canvas.toDataURL('image/png');

      // Bounding box around Chamoli region
      const west = 79.18;
      const south = 30.32;
      const east = 79.46;
      const north = 30.50;

      try {
        const provider = await Cesium.SingleTileImageryProvider.fromUrl(dataUrl, {
          rectangle: Cesium.Rectangle.fromDegrees(west, south, east, north)
        });

        if (cancelled || viewer.isDestroyed()) return;

        const layer = viewer.imageryLayers.addImageryProvider(provider);
        layer.alpha = 0.55;
        layerRef.current = layer;
        viewer.scene.requestRender();
      } catch (e) {
        console.warn('RiskHeatmap: failed to create imagery provider', e);
      }
    }

    addHeatmap();

    return () => {
      cancelled = true;
      if (layerRef.current && !viewer.isDestroyed()) {
        viewer.imageryLayers.remove(layerRef.current, true);
        layerRef.current = null;
      }
    };
  }, [viewer]);

  return null;
}
