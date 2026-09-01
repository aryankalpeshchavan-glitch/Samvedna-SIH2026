import React, { useRef, useEffect, useState } from 'react';
import * as Cesium from 'cesium';
import useStore from '../../store/useStore';
import { EPICENTER, IMPACT_RADIUS_KM } from '../../utils/constants';
import RiskHeatmap from './RiskHeatmap';
import ImpactZone from './ImpactZone';
import SensorMarkers from './SensorMarkers';
import DispatchUnits from './DispatchUnits';
import PersonMarkers from './PersonMarkers';
import PredictionCard from './PredictionCard';


const LAYER_LABELS = [
  { key: 'riskHeatmap', label: '🗺 Risk Heatmap' },
  { key: 'impactZone', label: '⭕ Impact Zone' },
  { key: 'sensors', label: '📡 Sensors' },
  { key: 'dispatchUnits', label: '🚗 Dispatch' },
  { key: 'persons', label: '👤 Persons' }
];

export default function CesiumMap({ socketRef }) {
  const containerRef = useRef(null);
  const viewerRef = useRef(null);
  const [viewerReady, setViewerReady] = useState(false);
  const layers = useStore((s) => s.layers);
  const toggleLayer = useStore((s) => s.toggleLayer);
  const showPrediction = useStore((s) => s.showPrediction);
  const selectedAlert = useStore((s) => s.selectedAlert);
  const selectedPerson = useStore((s) => s.selectedPerson);
  const selectedUnit = useStore((s) => s.selectedUnit);

  // Initialize Cesium Viewer
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    Cesium.Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_ION_TOKEN;

    const viewer = new Cesium.Viewer(containerRef.current, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      selectionIndicator: false,
      navigationHelpButton: false,
      animation: false,
      timeline: false,
      fullscreenButton: false,
      infoBox: false,
      requestRenderMode: true,
      maximumRenderTimeChange: Infinity,
      msaaSamples: 2
    });

    // Scene settings for performance and visuals
    const scene = viewer.scene;
    scene.globe.enableLighting = true;
    scene.fog.enabled = true;
    scene.fog.density = 0.0002;
    scene.globe.depthTestAgainstTerrain = true;
    scene.skyAtmosphere.hueShift = -0.05;
    scene.skyAtmosphere.saturationShift = -0.2;
    scene.skyAtmosphere.brightnessShift = -0.1;

    // Fly to Himalayan region (Chamoli)
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(79.32, 30.40, 25000),
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-45),
        roll: 0
      },
      duration: 2
    });

    viewerRef.current = viewer;
    setViewerReady(true);

    return () => {
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy();
      }
      viewerRef.current = null;
      setViewerReady(false);
    };
  }, []);

  // Handle flyTo when selection changes
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    let target = null;
    if (selectedAlert) target = { lng: selectedAlert.lng, lat: selectedAlert.lat };
    else if (selectedPerson) target = { lng: selectedPerson.lng, lat: selectedPerson.lat };
    else if (selectedUnit?.currentPosition) target = { lng: selectedUnit.currentPosition[0], lat: selectedUnit.currentPosition[1] };

    if (target) {
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(target.lng, target.lat, 8000),
        orientation: {
          heading: Cesium.Math.toRadians(0),
          pitch: Cesium.Math.toRadians(-55),
          roll: 0
        },
        duration: 1.5
      });
    }
  }, [selectedAlert, selectedPerson, selectedUnit]);

  return (
    <div className="map-container" id="map-container">
      <div id="cesiumContainer" ref={containerRef} />

      {/* Layer toggle chips */}
      <div className="layer-controls">
        {LAYER_LABELS.map(({ key, label }) => (
          <button
            key={key}
            className={`layer-chip ${layers[key] ? 'active' : ''}`}
            onClick={() => toggleLayer(key)}
            id={`layer-toggle-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Map sub-components — each manages its own Cesium entities */}
      {viewerReady && viewerRef.current && (
        <>
          {layers.riskHeatmap && <RiskHeatmap viewer={viewerRef.current} />}
          {layers.impactZone && <ImpactZone viewer={viewerRef.current} />}
          {layers.sensors && <SensorMarkers viewer={viewerRef.current} />}
          {layers.dispatchUnits && <DispatchUnits viewer={viewerRef.current} />}
          {layers.persons && <PersonMarkers viewer={viewerRef.current} />}
        </>
      )}

      {/* Prediction card overlay */}
      {showPrediction && <PredictionCard />}

      {/* Legend */}
      {layers.riskHeatmap && (
        <div className="map-legend" id="map-legend">
          <div className="legend-title">Risk Level</div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ff1a1a' }} />
            <span>Critical (&gt;90%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ff8c00' }} />
            <span>High (70-90%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ffd700' }} />
            <span>Moderate (40-70%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#2d8a2d' }} />
            <span>Low (&lt;40%)</span>
          </div>
        </div>
      )}
    </div>
  );
}
