import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import useStore from '../../store/useStore';

function createSparklineSvg(values, color = '#ECECEC') {
  if (!values || values.length < 2) return '';
  const w = 60, h = 20;
  const min = Math.min(...values);
  const max = Math.max(...values) || 1;
  const range = max - min || 1;
  const points = values.map((v, i) =>
    `${(i / (values.length - 1)) * w},${h - ((v - min) / range) * h}`
  ).join(' ');
  return `<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg"><polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/></svg>`;
}

export default function SensorMarkers({ viewer }) {
  const entityRefs = useRef([]);
  const popupRef = useRef(null);
  const sensors = useStore((s) => s.sensors);
  const sensorHistory = useStore((s) => s.sensorHistory);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || sensors.length === 0) return;

    // Remove old entities
    entityRefs.current.forEach((e) => {
      if (!viewer.isDestroyed()) viewer.entities.remove(e);
    });
    entityRefs.current = [];

    sensors.forEach((sensor) => {
      const position = Cesium.Cartesian3.fromDegrees(sensor.lng, sensor.lat);

      const entity = viewer.entities.add({
        position,
        id: `sensor-${sensor.id}`,
        point: {
          pixelSize: sensor.alert ? 10 : 7,
          color: sensor.alert ? Cesium.Color.WHITE : Cesium.Color.fromAlpha(Cesium.Color.WHITE, 0.6),
          outlineColor: sensor.alert ? Cesium.Color.RED.withAlpha(0.8) : Cesium.Color.fromAlpha(Cesium.Color.WHITE, 0.3),
          outlineWidth: sensor.alert ? 3 : 1,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(1000, 1.2, 50000, 0.5)
        },
        label: {
          text: sensor.name,
          font: '10px Inter, sans-serif',
          fillColor: Cesium.Color.fromAlpha(Cesium.Color.WHITE, 0.7),
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -14),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          scaleByDistance: new Cesium.NearFarScalar(1000, 1, 30000, 0.4),
          translucencyByDistance: new Cesium.NearFarScalar(1000, 1, 50000, 0)
        },
        description: buildDescription(sensor, sensorHistory[sensor.id])
      });

      entityRefs.current.push(entity);
    });

    viewer.scene.requestRender();

    return () => {
      entityRefs.current.forEach((e) => {
        if (!viewer.isDestroyed()) viewer.entities.remove(e);
      });
      entityRefs.current = [];
    };
  }, [viewer, sensors, sensorHistory]);

  return null;
}

function buildDescription(sensor, history) {
  const rainfallHistory = history ? history.map(h => h.rainfall) : [sensor.rainfall];
  const moistureHistory = history ? history.map(h => h.soilMoisture) : [sensor.soilMoisture];
  const tiltHistory = history ? history.map(h => h.tilt) : [sensor.tilt];

  return `
    <div style="font-family:Inter,sans-serif;background:#2f2f2f;color:#ececec;padding:12px;border-radius:8px;min-width:200px;">
      <div style="font-weight:700;font-size:14px;margin-bottom:8px;">${sensor.name}</div>
      <div style="font-size:12px;color:#9a9a9a;margin-bottom:4px;">Station ${sensor.id}</div>
      ${sensor.alert ? '<div style="color:#ff4444;font-weight:600;font-size:11px;margin-bottom:8px;">⚠ ALERT STATE</div>' : ''}
      <table style="width:100%;font-size:12px;border-collapse:collapse;">
        <tr style="border-bottom:1px solid #444;">
          <td style="padding:4px 0;color:#9a9a9a;">🌧 Rainfall</td>
          <td style="padding:4px 0;text-align:right;font-weight:600;">${sensor.rainfall} mm/hr</td>
        </tr>
        <tr style="border-bottom:1px solid #444;">
          <td style="padding:4px 0;color:#9a9a9a;">💧 Soil Moisture</td>
          <td style="padding:4px 0;text-align:right;font-weight:600;">${sensor.soilMoisture}%</td>
        </tr>
        <tr>
          <td style="padding:4px 0;color:#9a9a9a;">📐 Tilt</td>
          <td style="padding:4px 0;text-align:right;font-weight:600;">${sensor.tilt}°</td>
        </tr>
      </table>
    </div>
  `;
}
