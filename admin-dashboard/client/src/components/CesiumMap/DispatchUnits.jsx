import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import useStore from '../../store/useStore';

const UNIT_ICONS = {
  'Rescue Team': '🚒',
  'Medical Unit': '🚑',
  'Helicopter': '🚁',
  'Engineering': '🔧'
};

function createBillboardCanvas(icon, status) {
  const size = 40;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  // Background circle
  ctx.beginPath();
  ctx.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
  ctx.fillStyle = status === 'ON SITE' ? '#ffffff' : status === 'EN ROUTE' ? '#d4d4d4' : '#555';
  ctx.fill();
  ctx.strokeStyle = status === 'ON SITE' ? '#4ade80' : '#888';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Icon text
  ctx.font = '20px serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(icon, size / 2, size / 2);

  return canvas;
}

export default function DispatchUnits({ viewer }) {
  const entityRefs = useRef({});
  const units = useStore((s) => s.units);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || units.length === 0) return;

    units.forEach((unit) => {
      const pos = unit.currentPosition || unit.route?.[unit.currentRouteIndex || 0];
      if (!pos) return;

      const position = Cesium.Cartesian3.fromDegrees(pos[0], pos[1], 100);
      const icon = UNIT_ICONS[unit.type] || '🚗';
      const canvas = createBillboardCanvas(icon, unit.status);

      if (entityRefs.current[unit.id]) {
        // Update existing entity position
        const entity = entityRefs.current[unit.id];
        entity.position = position;
        entity.billboard.image = canvas;
      } else {
        // Create new entity
        const entity = viewer.entities.add({
          id: `unit-${unit.id}`,
          position,
          billboard: {
            image: canvas,
            width: 36,
            height: 36,
            verticalOrigin: Cesium.VerticalOrigin.CENTER,
            horizontalOrigin: Cesium.HorizontalOrigin.CENTER,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
          },
          label: {
            text: unit.id,
            font: '10px Inter, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.TOP,
            pixelOffset: new Cesium.Cartesian2(0, 22),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            scaleByDistance: new Cesium.NearFarScalar(1000, 1, 30000, 0.4)
          }
        });
        entityRefs.current[unit.id] = entity;
      }
    });

    // Draw route lines for EN ROUTE units
    units.forEach((unit) => {
      const lineId = `route-${unit.id}`;
      if (unit.status === 'EN ROUTE' && unit.route && unit.route.length > 1) {
        if (!entityRefs.current[lineId]) {
          const positions = unit.route.map(([lng, lat]) =>
            Cesium.Cartesian3.fromDegrees(lng, lat, 50)
          );
          const routeLine = viewer.entities.add({
            id: lineId,
            polyline: {
              positions,
              width: 4,
              material: Cesium.Color.fromCssColorString('#3b82f6').withAlpha(0.9),
              clampToGround: false
            }
          });
          entityRefs.current[lineId] = routeLine;
        }
      }
    });

    viewer.scene.requestRender();
  }, [viewer, units]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      Object.values(entityRefs.current).forEach((e) => {
        if (viewer && !viewer.isDestroyed()) viewer.entities.remove(e);
      });
      entityRefs.current = {};
    };
  }, [viewer]);

  return null;
}
