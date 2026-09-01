import { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import useStore from '../../store/useStore';

export default function PersonMarkers({ viewer }) {
  const entityRefs = useRef([]);
  const persons = useStore((s) => s.persons);

  useEffect(() => {
    if (!viewer || viewer.isDestroyed() || persons.length === 0) return;

    // Remove old entities
    entityRefs.current.forEach((e) => {
      if (!viewer.isDestroyed()) viewer.entities.remove(e);
    });
    entityRefs.current = [];

    persons.forEach((person) => {
      const position = Cesium.Cartesian3.fromDegrees(person.lng, person.lat);
      const inZone = person.status === 'IN ZONE';

      const entity = viewer.entities.add({
        position,
        id: `person-marker-${person.id}`,
        point: {
          pixelSize: inZone ? 8 : 5,
          color: inZone ? Cesium.Color.WHITE : Cesium.Color.fromAlpha(Cesium.Color.WHITE, 0.5),
          outlineColor: inZone ? Cesium.Color.RED.withAlpha(0.8) : Cesium.Color.TRANSPARENT,
          outlineWidth: inZone ? 3 : 0,
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(1000, 1.2, 80000, 0.3)
        },
        label: inZone ? {
          text: person.name.split(' ')[0],
          font: '10px Inter, sans-serif',
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -12),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(1000, 1, 20000, 0),
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
        } : undefined
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
  }, [viewer, persons]);

  return null;
}
