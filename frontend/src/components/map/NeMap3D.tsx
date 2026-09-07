import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import { getNeStatesGeoJson, MONITORING_POINTS, NE_CENTER, NORTHEAST_STATES } from '../../data/northeastGeoData';
import { CITIZEN_MAP_REPORTS, MOCK_SAFE_ROUTE } from '../../data/mockStoryData';
import { MapLayerMode, MapViewStyle, NeStateInfo, MonitoringPoint } from '../../types/map';
import { CitizenMapReport } from '../../types/emergency';
import { RainCanvasOverlay } from './RainCanvasOverlay';
import { useTranslation } from '../../i18n/LanguageContext';
import { Loader2, AlertOctagon } from 'lucide-react';
import { RiskZoneOut, classifyRiskLevel } from '../../types/api';

interface NeMap3DProps {
  mapViewStyle?: MapViewStyle;
  layerMode: MapLayerMode;
  selectedState: NeStateInfo | null;
  selectedStation: MonitoringPoint | null;
  selectedCitizenReport: CitizenMapReport | null;
  selectedRiskZone?: RiskZoneOut | null;
  riskZones?: RiskZoneOut[];
  isRiskLoading?: boolean;
  riskError?: string | null;
  onRetryRisk?: () => void;
  showSafeRoute: boolean;
  userLocation: [number, number] | null; // [lng, lat]
  onSelectState: (state: NeStateInfo | null) => void;
  onSelectStation: (station: MonitoringPoint | null) => void;
  onSelectCitizenReport: (report: CitizenMapReport | null) => void;
  onSelectRiskZone?: (zone: RiskZoneOut | null) => void;
  onHoverState: (stateName: string | null) => void;
}

function computeStateRiskLevel(state: NeStateInfo, zones: RiskZoneOut[]): 'LOW' | 'MEDIUM' | 'HIGH' {
  if (!zones || zones.length === 0) return 'LOW';
  const matching = zones.filter((z) => {
    if (z.state && z.state.toLowerCase() === state.id.toLowerCase()) return true;
    if (z.lat != null && z.lng != null) {
      const dist = Math.hypot(z.lat - state.center[0], z.lng - state.center[1]);
      return dist < 1.5;
    }
    return false;
  });
  if (matching.length === 0) return 'LOW';
  const maxScore = Math.max(...matching.map((z) => z.risk_score));
  return classifyRiskLevel(maxScore);
}

function getNeStatesGeoJsonWithLiveRisk(zones: RiskZoneOut[] = []) {
  return {
    type: 'FeatureCollection',
    features: NORTHEAST_STATES.map((state) => ({
      type: 'Feature',
      id: state.id,
      properties: {
        id: state.id,
        name: state.name,
        code: state.code,
        riskLevel: computeStateRiskLevel(state, zones),
        avgRainfall: state.avgRainfall24h,
        soilMoisture: state.avgSoilMoisture,
        elevationRange: state.elevationRange,
        heightOffset: state.heightOffset,
      },
      geometry: {
        type: 'Polygon',
        coordinates: state.polygonCoords,
      },
    })),
  };
}

// 1. Single Continuous 2D Overhead High-Resolution Satellite Hybrid Map Style (Satellite + Roads + Cities/Towns/Places)
const SATELLITE_HYBRID_MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    'satellite-base': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      maxzoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, USDA, USGS',
    },
    'hybrid-transportation': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
        'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      maxzoom: 19,
    },
    'hybrid-labels': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      maxzoom: 19,
    },
  },
  layers: [
    {
      id: 'satellite-base-layer',
      type: 'raster',
      source: 'satellite-base',
      minzoom: 0,
      maxzoom: 22,
    },
  ],
};

// 2. Original CrisisCore Warm Cartographic 3D DEM Terrain Relief Map Style
const WARM_TERRAIN_MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    'carto-light': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap contributors',
    },
    'terrain-dem': {
      type: 'raster-dem',
      tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
      tileSize: 256,
      encoding: 'terrarium',
      maxzoom: 14,
    },
  },
  layers: [
    {
      id: 'carto-light-layer',
      type: 'raster',
      source: 'carto-light',
      minzoom: 0,
      maxzoom: 22,
    },
    {
      id: 'hills',
      type: 'hillshade',
      source: 'terrain-dem',
      paint: {
        'hillshade-exaggeration': 0.75,
        'hillshade-shadow-color': '#71856B',
        'hillshade-highlight-color': '#FAF9F3',
        'hillshade-accent-color': '#A87C58',
      },
    },
  ],
  terrain: {
    source: 'terrain-dem',
    exaggeration: 2.5,
  },
};

function setupMapSourcesAndLayers(map: maplibregl.Map, styleMode: MapViewStyle, showSafeRoute: boolean, riskZones: RiskZoneOut[] = []) {
  if (!map.getSource('ne-states-source')) {
    map.addSource('ne-states-source', {
      type: 'geojson',
      /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
      data: getNeStatesGeoJsonWithLiveRisk(riskZones) as any,
      generateId: true,
    });
  }

  if (!map.getSource('safe-route-source')) {
    map.addSource('safe-route-source', {
      type: 'geojson',
      data: {
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: MOCK_SAFE_ROUTE.safePathCoords,
        },
      },
    });
  }

  if (styleMode === 'satellite') {
    if (map.getTerrain()) map.setTerrain(null);

    // Layer 1: Subtle Translucent 2D Risk Area Polygon Fill Overlay (15% - 28% opacity)
    if (!map.getLayer('ne-states-fill')) {
      map.addLayer({
        id: 'ne-states-fill',
        type: 'fill',
        source: 'ne-states-source',
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            '#23483A',
            ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
            ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
            ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
            '#23483A',
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.28,
            0.15,
          ],
        },
      });
    }

    // Layer 2: Thin Clean 2D Risk Boundary Lines
    if (!map.getLayer('ne-states-line')) {
      map.addLayer({
        id: 'ne-states-line',
        type: 'line',
        source: 'ne-states-source',
        paint: {
          'line-color': [
            'case',
            ['==', ['get', 'riskLevel'], 'CRITICAL'], '#FF5252',
            ['==', ['get', 'riskLevel'], 'HIGH'], '#FF7A59',
            ['==', ['get', 'riskLevel'], 'WATCH'], '#FFC107',
            '#66BB6A',
          ],
          'line-width': 1.2,
          'line-opacity': 0.60,
        },
      });
    }

    // Layer 3: Safe Route Line Layer (Green Evacuation Corridor)
    if (!map.getLayer('safe-route-line')) {
      map.addLayer({
        id: 'safe-route-line',
        type: 'line',
        source: 'safe-route-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#00FF66',
          'line-width': 4.5,
          'line-dasharray': [2, 1],
          'line-opacity': showSafeRoute ? 0.95 : 0,
        },
      });
    }

    // Layer 4: Hybrid Roads & Transportation Network Overlay
    if (!map.getLayer('hybrid-transportation-layer') && map.getSource('hybrid-transportation')) {
      map.addLayer({
        id: 'hybrid-transportation-layer',
        type: 'raster',
        source: 'hybrid-transportation',
        minzoom: 0,
        maxzoom: 22,
        paint: {
          'raster-opacity': 0.85,
        },
      });
    }

    // Layer 5: Hybrid Place Names, City/Town Labels & State Boundaries Overlay
    if (!map.getLayer('hybrid-labels-layer') && map.getSource('hybrid-labels')) {
      map.addLayer({
        id: 'hybrid-labels-layer',
        type: 'raster',
        source: 'hybrid-labels',
        minzoom: 0,
        maxzoom: 22,
        paint: {
          'raster-opacity': 0.95,
        },
      });
    }
  } else {
    // Terrain 3D DEM Relief Setup
    map.setTerrain({
      source: 'terrain-dem',
      exaggeration: 2.5,
    });

    if (!map.getLayer('ne-states-fill')) {
      map.addLayer(
        {
          id: 'ne-states-fill',
          type: 'fill',
          source: 'ne-states-source',
          paint: {
            'fill-color': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              '#23483A',
              ['==', ['get', 'riskLevel'], 'CRITICAL'], '#5C1D1A',
              ['==', ['get', 'riskLevel'], 'HIGH'], '#8A3525',
              ['==', ['get', 'riskLevel'], 'WATCH'], '#965C22',
              '#183328',
            ],
            'fill-opacity': [
              'case',
              ['boolean', ['feature-state', 'hover'], false],
              0.45,
              0.25,
            ],
          },
        },
        'hills'
      );
    }

    if (!map.getLayer('ne-states-extrusion')) {
      map.addLayer({
        id: 'ne-states-extrusion',
        type: 'fill-extrusion',
        source: 'ne-states-source',
        paint: {
          'fill-extrusion-color': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            '#23483A',
            ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
            ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
            ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
            '#23483A',
          ],
          'fill-extrusion-height': [
            'case',
            ['==', ['get', 'riskLevel'], 'CRITICAL'], 35000,
            ['==', ['get', 'riskLevel'], 'HIGH'], 24000,
            ['==', ['get', 'riskLevel'], 'WATCH'], 15000,
            8000,
          ],
          'fill-extrusion-base': 0,
          'fill-extrusion-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.68,
            0.45,
          ],
          'fill-extrusion-vertical-gradient': true,
        },
      });
    }

    if (!map.getLayer('ne-states-line')) {
      map.addLayer({
        id: 'ne-states-line',
        type: 'line',
        source: 'ne-states-source',
        paint: {
          'line-color': '#101412',
          'line-width': 1.6,
          'line-dasharray': [4, 2],
          'line-opacity': 0.85,
        },
      });
    }

    if (!map.getLayer('safe-route-line')) {
      map.addLayer({
        id: 'safe-route-line',
        type: 'line',
        source: 'safe-route-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#23483A',
          'line-width': 4,
          'line-dasharray': [2, 1],
          'line-opacity': showSafeRoute ? 0.95 : 0,
        },
      });
    }
  }
}

export const NeMap3D: React.FC<NeMap3DProps> = ({
  mapViewStyle = 'satellite',
  layerMode,
  selectedState,
  selectedStation,
  selectedCitizenReport,
  selectedRiskZone,
  riskZones = [],
  isRiskLoading = false,
  riskError = null,
  onRetryRisk,
  showSafeRoute,
  userLocation,
  onSelectState,
  onSelectStation,
  onSelectCitizenReport,
  onSelectRiskZone,
  onHoverState,
}) => {
  const { t, language } = useTranslation();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const stationMarkersRef = useRef<maplibregl.Marker[]>([]);
  const citizenMarkersRef = useRef<maplibregl.Marker[]>([]);
  const riskMarkersRef = useRef<maplibregl.Marker[]>([]);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);
  const [isMapLoading, setIsMapLoading] = useState(true);

  // Maintain stable callback refs to avoid destroying & recreating the map on every parent render
  const onHoverStateRef = useRef(onHoverState);
  const onSelectStateRef = useRef(onSelectState);
  const onSelectStationRef = useRef(onSelectStation);
  const onSelectCitizenReportRef = useRef(onSelectCitizenReport);
  const onSelectRiskZoneRef = useRef(onSelectRiskZone);
  const riskZonesRef = useRef(riskZones);

  useEffect(() => {
    onHoverStateRef.current = onHoverState;
    onSelectStateRef.current = onSelectState;
    onSelectStationRef.current = onSelectStation;
    onSelectCitizenReportRef.current = onSelectCitizenReport;
    onSelectRiskZoneRef.current = onSelectRiskZone;
    riskZonesRef.current = riskZones;
  });

  // Initialize MapLibre GL JS Map Instance ONCE on component mount
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const initialStyle = mapViewStyle === 'terrain' ? WARM_TERRAIN_MAP_STYLE : SATELLITE_HYBRID_MAP_STYLE;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: initialStyle,
      center: NE_CENTER,
      zoom: 6.3,
      pitch: mapViewStyle === 'terrain' ? 52 : 0,
      bearing: mapViewStyle === 'terrain' ? -14 : 0,
      maxPitch: mapViewStyle === 'terrain' ? 85 : 0,
      minZoom: 4.5,
      maxZoom: 18,
      fadeDuration: 0,     // Instant tile swap on zoom without slow blur cross-fading
      maxTileCacheSize: 120, // High-performance tile memory caching
      renderWorldCopies: false,
      maxBounds: [
        [68.0, 6.0],       // Southwest coordinates [lng, lat] (India / Arabian Sea)
        [100.0, 37.0],      // Northeast coordinates [lng, lat] (NE Region / Border)
      ],
      attributionControl: false,
    });

    mapRef.current = map;

    // Handle container resize cleanly
    const handleResize = () => {
      if (mapRef.current) {
        mapRef.current.resize();
      }
    };
    window.addEventListener('resize', handleResize);

    map.on('load', () => {
      setIsMapLoading(false);
      setupMapSourcesAndLayers(map, mapViewStyle, showSafeRoute, riskZonesRef.current);

      // Hover Interactions for States using stable ref
      const handleMouseMove = (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features.length > 0) {
          map.getCanvas().style.cursor = 'pointer';
          const feature = e.features[0];
          onHoverStateRef.current(feature.properties?.name || null);

          if (hoveredIdRef.current !== null) {
            map.setFeatureState(
              { source: 'ne-states-source', id: hoveredIdRef.current },
              { hover: false }
            );
          }
          hoveredIdRef.current = feature.id as string | number;
          map.setFeatureState(
            { source: 'ne-states-source', id: hoveredIdRef.current },
            { hover: true }
          );
        }
      };

      const handleMouseLeave = () => {
        map.getCanvas().style.cursor = '';
        onHoverStateRef.current(null);
        if (hoveredIdRef.current !== null) {
          map.setFeatureState(
            { source: 'ne-states-source', id: hoveredIdRef.current },
            { hover: false }
          );
        }
        hoveredIdRef.current = null;
      };

      const handleClick = (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features.length > 0) {
          const stateId = e.features[0].properties?.id;
          const foundState = NORTHEAST_STATES.find((s) => s.id === stateId);
          if (foundState) {
            onSelectStateRef.current(foundState);
            onSelectStationRef.current(null);
            onSelectCitizenReportRef.current(null);
            map.flyTo({
              center: [foundState.center[1], foundState.center[0]],
              zoom: 7.5,
              pitch: mapViewStyle === 'terrain' ? 52 : 0,
              bearing: mapViewStyle === 'terrain' ? -14 : 0,
              duration: 1200,
            });
          }
        }
      };

      map.on('mousemove', 'ne-states-fill', handleMouseMove);
      map.on('mouseleave', 'ne-states-fill', handleMouseLeave);
      map.on('click', 'ne-states-fill', handleClick);

      // Monitoring Station Markers
      MONITORING_POINTS.forEach((station) => {
        const el = document.createElement('div');
        el.className = 'group relative cursor-pointer z-30';

        const colorBg =
          station.riskLevel === 'CRITICAL' || station.riskLevel === 'HIGH'
            ? 'bg-[#C6533C]'
            : station.riskLevel === 'WATCH'
            ? 'bg-[#D88A32]'
            : 'bg-[#23483A]';

        el.innerHTML = `
          <div class="relative flex items-center justify-center">
            <span class="animate-ping absolute inline-flex h-5 w-5 rounded-full opacity-60 ${colorBg}"></span>
            <div class="relative inline-flex rounded-full h-4 w-4 border-2 border-[#FAF9F3] items-center justify-center font-mono text-[8px] font-black text-white shadow-md ${colorBg}">
              ●
            </div>
          </div>
        `;

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          onSelectStationRef.current(station);
          onSelectStateRef.current(null);
          onSelectCitizenReportRef.current(null);
          map.flyTo({
            center: [station.lng, station.lat],
            zoom: 8.5,
            pitch: mapViewStyle === 'terrain' ? 50 : 0,
            bearing: mapViewStyle === 'terrain' ? -14 : 0,
            duration: 1200,
          });
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([station.lng, station.lat])
          .addTo(map);

        stationMarkersRef.current.push(marker);
      });

      // Citizen Report Markers
      CITIZEN_MAP_REPORTS.forEach((report) => {
        const el = document.createElement('div');
        el.className = 'group relative cursor-pointer z-30';
        const label = t(`hazards.${report.category}`);
        el.innerHTML = `
          <div class="relative flex flex-col items-center">
            <div class="px-2 py-1 bg-[#FAF9F3] border border-[#A87C58] rounded-md shadow-md text-[10px] font-mono font-bold text-[#202622] flex items-center space-x-1">
              <span>📍</span>
              <span class="report-marker-text" data-category="${report.category}">${label}</span>
            </div>
          </div>
        `;

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          onSelectCitizenReportRef.current(report);
          onSelectStateRef.current(null);
          onSelectStationRef.current(null);
          map.flyTo({
            center: [report.lng, report.lat],
            zoom: 9.0,
            pitch: mapViewStyle === 'terrain' ? 45 : 0,
            bearing: mapViewStyle === 'terrain' ? -14 : 0,
            duration: 1200,
          });
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([report.lng, report.lat])
          .addTo(map);

        citizenMarkersRef.current.push(marker);
      });
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      stationMarkersRef.current.forEach((m) => m.remove());
      citizenMarkersRef.current.forEach((m) => m.remove());
      riskMarkersRef.current.forEach((m) => m.remove());
      if (userMarkerRef.current) userMarkerRef.current.remove();
      map.remove();
    };
  }, []); // Mount ONCE with empty dependency array!

  // Dynamically update map style and camera perspective when switching between Satellite and Terrain modes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const currentCenter = map.getCenter();
    const currentZoom = map.getZoom();

    if (mapViewStyle === 'satellite') {
      map.setStyle(SATELLITE_HYBRID_MAP_STYLE);
      map.setMaxPitch(0);
      map.setPitch(0);
      map.setBearing(0);
    } else {
      map.setStyle(WARM_TERRAIN_MAP_STYLE);
      map.setMaxPitch(85);
      map.setPitch(52);
      map.setBearing(-14);
    }

    map.once('style.load', () => {
      map.jumpTo({ center: currentCenter, zoom: currentZoom });
      setupMapSourcesAndLayers(map, mapViewStyle, showSafeRoute, riskZonesRef.current);
    });
  }, [mapViewStyle, showSafeRoute]);

  // Live update map marker text when language changes without re-creating map
  useEffect(() => {
    citizenMarkersRef.current.forEach((marker) => {
      const labelSpan = marker.getElement().querySelector('.report-marker-text');
      if (labelSpan) {
        const cat = labelSpan.getAttribute('data-category');
        if (cat) {
          labelSpan.textContent = t(`hazards.${cat}`);
        }
      }
    });
  }, [t, language]);

  // Update Safe Route visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('safe-route-line')) {
      map.setPaintProperty('safe-route-line', 'line-opacity', showSafeRoute ? 0.95 : 0);
    }
  }, [showSafeRoute]);

  // Update User Location Ring Marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userLocation) return;

    if (!userMarkerRef.current) {
      const el = document.createElement('div');
      el.className = 'relative flex items-center justify-center z-30';
      el.innerHTML = `
        <span class="animate-ping absolute inline-flex h-8 w-8 rounded-full bg-[#23483A] opacity-40"></span>
        <span class="animate-pulse absolute inline-flex h-5 w-5 rounded-full border-2 border-[#23483A]"></span>
        <div class="relative w-3 h-3 rounded-full bg-[#23483A] border-2 border-[#FAF9F3]"></div>
      `;
      userMarkerRef.current = new maplibregl.Marker({ element: el })
        .setLngLat(userLocation)
        .addTo(map);
    } else {
      userMarkerRef.current.setLngLat(userLocation);
    }
  }, [userLocation]);

  // Update Layer mode paint properties for 2D/3D Risk / Rainfall Overlay
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('ne-states-fill')) {
      if (layerMode === 'risk' || layerMode === 'terrain') {
        map.setPaintProperty('ne-states-fill', 'fill-color', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          '#23483A',
          ['==', ['get', 'riskLevel'], 'CRITICAL'], mapViewStyle === 'terrain' ? '#5C1D1A' : '#8E2F2B',
          ['==', ['get', 'riskLevel'], 'HIGH'], mapViewStyle === 'terrain' ? '#8A3525' : '#C6533C',
          ['==', ['get', 'riskLevel'], 'WATCH'], mapViewStyle === 'terrain' ? '#965C22' : '#D88A32',
          '#23483A',
        ]);
        map.setPaintProperty('ne-states-fill', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          mapViewStyle === 'terrain' ? 0.45 : 0.28,
          mapViewStyle === 'terrain' ? 0.25 : 0.15,
        ]);
      } else if (layerMode === 'rainfall') {
        map.setPaintProperty('ne-states-fill', 'fill-color', '#536A72');
        map.setPaintProperty('ne-states-fill', 'fill-opacity', 0.20);
      }
    }
  }, [layerMode, mapViewStyle]);

  // Fly camera to selection cleanly
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (selectedStation) {
      map.flyTo({
        center: [selectedStation.lng, selectedStation.lat],
        zoom: 8.5,
        pitch: mapViewStyle === 'terrain' ? 50 : 0,
        bearing: mapViewStyle === 'terrain' ? -14 : 0,
        duration: 1200,
      });
    } else if (selectedState) {
      map.flyTo({
        center: [selectedState.center[1], selectedState.center[0]],
        zoom: 7.5,
        pitch: mapViewStyle === 'terrain' ? 52 : 0,
        bearing: mapViewStyle === 'terrain' ? -14 : 0,
        duration: 1400,
      });
    }
  }, [selectedState, selectedStation, mapViewStyle]);

  // Fly camera to selected risk zone
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedRiskZone || selectedRiskZone.lat == null || selectedRiskZone.lng == null) return;

    map.flyTo({
      center: [selectedRiskZone.lng, selectedRiskZone.lat],
      zoom: 8.5,
      pitch: mapViewStyle === 'terrain' ? 50 : 0,
      bearing: mapViewStyle === 'terrain' ? -14 : 0,
      duration: 1200,
    });
  }, [selectedRiskZone, mapViewStyle]);

  // Render Live Risk Markers on MapLibre
  useEffect(() => {
    const map = mapRef.current;
    if (!map || isMapLoading) return;

    // Clear previous live risk markers
    riskMarkersRef.current.forEach((m) => m.remove());
    riskMarkersRef.current = [];

    // Dynamically update state boundary polygon live risk levels based on real ML data
    const stateSource = map.getSource('ne-states-source') as maplibregl.GeoJSONSource | undefined;
    if (stateSource && stateSource.setData) {
      /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
      stateSource.setData(getNeStatesGeoJsonWithLiveRisk(riskZones) as any);
    }

    if (!riskZones || riskZones.length === 0) return;

    riskZones.forEach((zone) => {
      if (zone.lat == null || zone.lng == null) return;
      const category = classifyRiskLevel(zone.risk_score);
      const colorBg =
        category === 'HIGH'
          ? 'bg-[#C6533C]'
          : category === 'MEDIUM'
          ? 'bg-[#D88A32]'
          : 'bg-[#23483A]';

      const borderColor =
        category === 'HIGH'
          ? 'border-[#C6533C]'
          : category === 'MEDIUM'
          ? 'border-[#D88A32]'
          : 'border-[#23483A]';

      const el = document.createElement('div');
      el.className = 'group relative cursor-pointer z-30';
      el.setAttribute('data-testid', `risk-zone-${zone.id}`);

      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <span class="animate-ping absolute inline-flex h-6 w-6 rounded-full opacity-60 ${colorBg}"></span>
          <div class="relative inline-flex rounded-full h-5 w-5 border-2 border-[#FAF9F3] items-center justify-center font-mono text-[9px] font-black text-white shadow-lg ${colorBg}">
            ●
          </div>
          <div class="absolute -bottom-6 px-1.5 py-0.5 rounded bg-[#202622]/90 text-white font-mono text-[9px] font-bold whitespace-nowrap shadow border ${borderColor} opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            ${category} (${(zone.risk_score * 100).toFixed(0)}%)
          </div>
        </div>
      `;

      el.addEventListener('click', (ev) => {
        ev.stopPropagation();
        onSelectRiskZoneRef.current?.(zone);
        onSelectStateRef.current(null);
        onSelectStationRef.current(null);
        onSelectCitizenReportRef.current(null);
        map.flyTo({
          center: [zone.lng!, zone.lat!],
          zoom: 8.5,
          pitch: mapViewStyle === 'terrain' ? 50 : 0,
          bearing: mapViewStyle === 'terrain' ? -14 : 0,
          duration: 1200,
        });
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([zone.lng, zone.lat])
        .addTo(map);

      riskMarkersRef.current.push(marker);
    });
  }, [riskZones, isMapLoading, mapViewStyle]);

  return (
    <div
      ref={mapContainerRef}
      className="relative w-full h-[85vh] sm:h-[88vh] min-h-[500px] rounded-2xl overflow-hidden shadow-lg border border-[#C7B89B]/40 bg-[#101412]"
    >
      {/* Live ML Risk Status Indicator Overlay */}
      <div className="absolute top-3 left-3 z-20 pointer-events-auto">
        {isRiskLoading ? (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#202622]/90 backdrop-blur-md border border-[#C7B89B]/40 text-[#FAF9F3] shadow-md text-xs font-mono">
            <Loader2 className="w-3.5 h-3.5 text-[#D88A32] animate-spin" />
            <span>Fetching live ML risk data...</span>
          </div>
        ) : riskError ? (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#8E2F2B]/95 backdrop-blur-md border border-[#FF5252]/50 text-white shadow-lg text-xs font-mono">
            <AlertOctagon className="w-4 h-4 text-red-200 shrink-0" />
            <span className="max-w-[220px] truncate">Risk API Error: {riskError}</span>
            {onRetryRisk && (
              <button
                onClick={onRetryRisk}
                className="ml-1 px-2 py-0.5 rounded bg-white/20 hover:bg-white/30 text-[10px] font-bold cursor-pointer transition-colors"
              >
                Retry
              </button>
            )}
          </div>
        ) : riskZones && riskZones.length > 0 ? (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#202622]/90 backdrop-blur-md border border-[#23483A]/80 text-[#FAF9F3] shadow-md text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-[#00FF66] animate-pulse"></span>
            <span>Live ML Risk: {riskZones.length} Zone{riskZones.length > 1 ? 's' : ''} Active</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-[#202622]/85 backdrop-blur-md border border-[#C7B89B]/30 text-[#FAF9F3]/90 shadow-md text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            <span>Live ML Risk: 0 active zones</span>
          </div>
        )}
      </div>

      {/* Subtle Map Loading Overlay */}
      {isMapLoading && (
        <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-[#101412]/85 backdrop-blur-sm text-[#FAF9F3] transition-opacity duration-300 pointer-events-none">
          <div className="flex items-center space-x-2.5 px-4 py-2.5 rounded-xl bg-[#202622]/90 border border-[#C7B89B]/30 shadow-lg">
            <Loader2 className="w-4 h-4 text-[#D88A32] animate-spin" />
            <span className="text-xs font-mono font-bold tracking-wide">Loading Satellite Map...</span>
          </div>
        </div>
      )}

      <RainCanvasOverlay isActive={layerMode === 'rainfall'} />
    </div>
  );
};
