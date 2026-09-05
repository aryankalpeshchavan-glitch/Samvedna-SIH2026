import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import { EPICENTER, IMPACT_RADIUS_KM } from '../../utils/constants';
import useStore from '../../store/useStore';

export default function ImpactZone({ viewer }) {
  const entityRefs = useRef([]);
  const animStartRef = useRef(Date.now());
  const setShowPrediction = useStore((s) => s.setShowPrediction);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed()) return;

    const epicenterCart = Cesium.Cartesian3.fromDegrees(EPICENTER.lng, EPICENTER.lat);
    const targetRadius = IMPACT_RADIUS_KM * 1000; // meters
    animStartRef.current = Date.now();

    // Animated expanding circle — radius grows over 3 seconds
    const animatedRadius = new Cesium.CallbackProperty(() => {
      const elapsed = (Date.now() - animStartRef.current) / 1000;
      const t = Math.min(1, elapsed / 3);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      // Cesium requires semiMajorAxis > 0, so clamp to minimum 1m
      return Math.max(1, targetRadius * eased);
    }, false);

    // Pulsing outline
    const pulsingAlpha = new Cesium.CallbackProperty(() => {
      const t = (Date.now() % 2000) / 2000;
      return 0.4 + 0.6 * Math.abs(Math.sin(t * Math.PI));
    }, false);

    // Main impact circle
    const impactCircle = viewer.entities.add({
      position: epicenterCart,
      ellipse: {
        semiMajorAxis: animatedRadius,
        semiMinorAxis: animatedRadius,
        material: Cesium.Color.RED.withAlpha(0.15),
        outline: false,
        height: 0,
        classificationType: Cesium.ClassificationType.BOTH
      }
    });

    // Runout zone — elongated ellipse downslope (south-east direction)
    const runoutCenter = Cesium.Cartesian3.fromDegrees(
      EPICENTER.lng + 0.015,
      EPICENTER.lat - 0.025
    );

    const runoutEllipse = viewer.entities.add({
      position: runoutCenter,
      ellipse: {
        semiMajorAxis: 4500,
        semiMinorAxis: 1800,
        rotation: Cesium.Math.toRadians(-30),
        material: Cesium.Color.ORANGE.withAlpha(0.1),
        outline: false,
        height: 0,
        classificationType: Cesium.ClassificationType.BOTH
      }
    });

    // Epicenter marker
    const epicenterMarker = viewer.entities.add({
      position: epicenterCart,
      point: {
        pixelSize: 12,
        color: Cesium.Color.RED,
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      },
      label: {
        text: 'EPICENTER',
        font: '11px Inter, sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(0, -18),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
      }
    });

    entityRefs.current = [impactCircle, runoutEllipse, epicenterMarker];

    // Click handler to show prediction card
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((click) => {
      const picked = viewer.scene.pick(click.position);
      if (Cesium.defined(picked) && picked.id === impactCircle) {
        setShowPrediction(true);
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    // Keep rendering for animations
    const renderInterval = setInterval(() => {
      if (!viewer.isDestroyed()) viewer.scene.requestRender();
    }, 50);

    return () => {
      clearInterval(renderInterval);
      handler.destroy();
      entityRefs.current.forEach((e) => {
        if (!viewer.isDestroyed()) viewer.entities.remove(e);
      });
      entityRefs.current = [];
    };
  }, [viewer]);

  return null;
}
