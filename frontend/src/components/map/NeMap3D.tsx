import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import { getNeStatesGeoJson, MONITORING_POINTS, NE_CENTER, NORTHEAST_STATES } from '../../data/northeastGeoData';
import { CITIZEN_MAP_REPORTS, MOCK_SAFE_ROUTE } from '../../data/mockStoryData';
import { MapLayerMode, NeStateInfo, MonitoringPoint } from '../../types/map';
import { CitizenMapReport } from '../../types/emergency';

interface NeMap3DProps {
  layerMode: MapLayerMode;
  selectedState: NeStateInfo | null;
  selectedStation: MonitoringPoint | null;
  selectedCitizenReport: CitizenMapReport | null;
  showSafeRoute: boolean;
  userLocation: [number, number] | null; // [lng, lat]
  onSelectState: (state: NeStateInfo | null) => void;
  onSelectStation: (station: MonitoringPoint | null) => void;
  onSelectCitizenReport: (report: CitizenMapReport | null) => void;
  onHoverState: (stateName: string | null) => void;
  centerUserLocationTrigger?: number;
}

const WARM_CARTOGRAPHIC_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  projection: {
    type: 'globe',
  },
  sources: {
    'carto-light': {
      type: 'raster',
      tiles: [
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap contributors',
    },
    'carto-dark': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
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
      layout: { visibility: 'visible' },
    },
    {
      id: 'carto-dark-layer',
      type: 'raster',
      source: 'carto-dark',
      minzoom: 0,
      maxzoom: 22,
      layout: { visibility: 'none' },
      paint: {
        'raster-hue-rotate': 195,
        'raster-brightness-min': 0.04,
        'raster-brightness-max': 0.8,
        'raster-contrast': 0.35,
        'raster-saturation': 0.7,
      },
    },
    {
      id: 'hills',
      type: 'hillshade',
      source: 'terrain-dem',
      paint: {
        'hillshade-exaggeration': 0.85,
        'hillshade-shadow-color': '#71856B',
        'hillshade-highlight-color': '#FFFFFF',
        'hillshade-accent-color': '#A87C58',
      },
    },
  ],
  terrain: {
    source: 'terrain-dem',
    exaggeration: 3,
  },
};

export const NeMap3D: React.FC<NeMap3DProps> = ({
  layerMode,
  selectedState,
  selectedStation,
  selectedCitizenReport,
  showSafeRoute,
  userLocation,
  onSelectState,
  onSelectStation,
  onSelectCitizenReport,
  onHoverState,
  centerUserLocationTrigger,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const stationMarkersRef = useRef<maplibregl.Marker[]>([]);
  const citizenMarkersRef = useRef<maplibregl.Marker[]>([]);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);

  const [isDark, setIsDark] = React.useState(false);

  // Helper to create or update user location marker
  const updateUserLocationMarker = (map: maplibregl.Map, location: [number, number]) => {
    if (!userMarkerRef.current) {
      const el = document.createElement('div');
      el.className = 'group relative flex flex-col items-center justify-end cursor-pointer';
      // Pointer anchor should be at the bottom center of the div, so we make it taller
      el.style.width = '40px';
      el.style.height = '60px';
      el.style.zIndex = '9999';
      
      // Teardrop pointer pin SVG
      el.innerHTML = `
        <div class="absolute -bottom-2 w-4 h-2 bg-black/40 rounded-[100%] blur-[2px]"></div>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#00FF66" class="w-10 h-10 drop-shadow-lg stroke-white stroke-[1.5]">
          <path fill-rule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-1.99 3.963-4.98 3.963-8.827a8.25 8.25 0 00-16.5 0c0 3.846 2.02 6.837 3.963 8.827a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
        </svg>
      `;

      const popup = new maplibregl.Popup({ offset: 24, closeButton: false })
        .setHTML(`
          <div style="font-family: system-ui, sans-serif; font-size: 11px; font-weight: 800; color: #008000; text-transform: uppercase; letter-spacing: 0.5px; background: white; padding: 3px 8px; rounded: 6px;">
            📍 YOUR LOCATION
          </div>
        `);

      userMarkerRef.current = new maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat(location)
        .setPopup(popup)
        .addTo(map);

      // Open popup by default
      popup.addTo(map);
    } else {
      userMarkerRef.current.setLngLat(location);
      // Ensure the marker remains on the map during HMR or re-renders
      if (!userMarkerRef.current.getElement().parentNode) {
        userMarkerRef.current.addTo(map);
      }
    }
  };

  // Observe theme changes
  useEffect(() => {
    const checkDark = () => setIsDark(document.documentElement.classList.contains('dark'));
    checkDark();
    const observer = new MutationObserver(checkDark);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Initialize MapLibre GL JS Map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: WARM_CARTOGRAPHIC_STYLE,
      center: NE_CENTER,
      zoom: 6.8,
      pitch: 60,
      bearing: -10,
      maxPitch: 75,
      minZoom: 5.5,
      maxZoom: 18,
      attributionControl: false,
    });

    mapRef.current = map;

    map.on('load', () => {
      try {
        map.setProjection({ type: 'globe' });
      } catch (err) {
        console.warn('Globe projection error:', err);
      }
      // 1. Add NE States GeoJSON Source
      map.addSource('ne-states-source', {
        type: 'geojson',
        /* eslint-disable-next-line @typescript-eslint/no-explicit-any */
        data: getNeStatesGeoJson() as any,
        generateId: true,
      });

      // 2. Add Safe Evacuation Route GeoJSON Source
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

      // 3. Add Fill Layer (Warm Cartographic Palette)
      map.addLayer({
        id: 'ne-states-fill',
        type: 'fill',
        source: 'ne-states-source',
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            '#228B22', // Hovered State
            ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
            ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
            ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
            '#228B22', // Default Default State
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            0.65,
            0.35,
          ],
        },
      });

      // 4. Add Crisp Warm Boundary Lines
      map.addLayer({
        id: 'ne-states-line',
        type: 'line',
        source: 'ne-states-source',
        paint: {
          'line-color': '#228B22',
          'line-width': 1.8,
          'line-opacity': 0.85,
        },
      });

      // 5. Add Safe Route Line Layer (Green Forest Evacuation Corridor)
      map.addLayer({
        id: 'safe-route-line',
        type: 'line',
        source: 'safe-route-source',
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#228B22',
          'line-width': 4,
          'line-dasharray': [2, 1],
          'line-opacity': showSafeRoute ? 0.95 : 0,
        },
      });

      // 6. Hover Interactions
      map.on('mousemove', 'ne-states-fill', (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features.length > 0) {
          map.getCanvas().style.cursor = 'pointer';
          const feature = e.features[0];
          onHoverState(feature.properties?.name || null);

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
      });

      map.on('mouseleave', 'ne-states-fill', () => {
        map.getCanvas().style.cursor = '';
        onHoverState(null);
        if (hoveredIdRef.current !== null) {
          map.setFeatureState(
            { source: 'ne-states-source', id: hoveredIdRef.current },
            { hover: false }
          );
        }
        hoveredIdRef.current = null;
      });

      // 7. Click Selection
      map.on('click', 'ne-states-fill', (e: maplibregl.MapLayerMouseEvent) => {
        if (e.features && e.features.length > 0) {
          const stateId = e.features[0].properties?.id;
          const foundState = NORTHEAST_STATES.find((s) => s.id === stateId);
          if (foundState) {
            onSelectState(foundState);
            onSelectStation(null);
            onSelectCitizenReport(null);
            map.flyTo({
              center: [foundState.center[1], foundState.center[0]],
              zoom: 7.5,
              pitch: 52,
              duration: 1400,
            });
          }
        }
      });

      // 8. Monitoring Station Markers (Muted Cartographic Pins)
      MONITORING_POINTS.forEach((station) => {
        const el = document.createElement('div');
        el.className = 'group relative cursor-pointer';

        const colorBg =
          station.riskLevel === 'CRITICAL' || station.riskLevel === 'HIGH'
            ? 'bg-[#C6533C]'
            : station.riskLevel === 'WATCH'
            ? 'bg-[#D88A32]'
            : 'bg-accent';

        el.innerHTML = `
          <div class="relative flex items-center justify-center">
            <span class="animate-ping absolute inline-flex h-5 w-5 rounded-full opacity-60 ${colorBg}"></span>
            <div class="relative inline-flex rounded-full h-4 w-4 border-2 border-surface items-center justify-center font-mono text-[8px] font-black text-white shadow-md ${colorBg}">
              ●
            </div>
          </div>
        `;

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          onSelectStation(station);
          onSelectState(null);
          onSelectCitizenReport(null);
          map.flyTo({
            center: [station.lng, station.lat],
            zoom: 8.5,
            pitch: 50,
            duration: 1200,
          });
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([station.lng, station.lat])
          .addTo(map);

        stationMarkersRef.current.push(marker);
      });

      // 9. Citizen Report Markers on Map
      CITIZEN_MAP_REPORTS.forEach((report) => {
        const el = document.createElement('div');
        el.className = 'group relative cursor-pointer';
        el.innerHTML = `
          <div class="px-2 py-1 bg-surface border border-border rounded-md shadow-md text-[10px] font-mono font-bold text-primary flex items-center space-x-1">
            <span>📍</span>
            <span>${report.category.replace('_', ' ')}</span>
          </div>
        `;

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          onSelectCitizenReport(report);
          onSelectState(null);
          onSelectStation(null);
          map.flyTo({
            center: [report.lng, report.lat],
            zoom: 9.0,
            pitch: 45,
            duration: 1200,
          });
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([report.lng, report.lat])
          .addTo(map);

        citizenMarkersRef.current.push(marker);
      });

      // 10. Initial User Location Marker
      if (userLocation) {
        updateUserLocationMarker(map, userLocation);
      }
    });

    return () => {
      stationMarkersRef.current.forEach((m) => m.remove());
      citizenMarkersRef.current.forEach((m) => m.remove());
      if (userMarkerRef.current) userMarkerRef.current.remove();
      map.remove();
    };
  }, [onHoverState, onSelectCitizenReport, onSelectState, onSelectStation]);

  // Update Safe Route visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('safe-route-line')) {
      map.setPaintProperty('safe-route-line', 'line-opacity', showSafeRoute ? 0.95 : 0);
    }
  }, [showSafeRoute]);

  // Auto-center on user location when real GPS coordinates are acquired
  const initialGpsFlyDoneRef = useRef(false);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userLocation || initialGpsFlyDoneRef.current) return;

    // Check if userLocation is different from the fallback Guwahati default
    if (userLocation[0] !== 91.7362 || userLocation[1] !== 26.1445) {
      initialGpsFlyDoneRef.current = true;
      map.flyTo({
        center: userLocation,
        zoom: 14,
        pitch: 50,
        duration: 1600,
      });
    }
  }, [userLocation]);

  // Update User Location Ring Marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userLocation) return;
    updateUserLocationMarker(map, userLocation);
  }, [userLocation]);

  // Fly to user location when "My Area" is clicked
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userLocation || !centerUserLocationTrigger) return;

    map.flyTo({
      center: userLocation,
      zoom: 14,
      pitch: 45,
      duration: 1500,
    });
  }, [centerUserLocationTrigger, userLocation]);

  // Update Layer mode paint properties and Tile Visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    // Toggle tile visibilities
    if (map.getLayer('carto-light-layer')) {
      map.setLayoutProperty('carto-light-layer', 'visibility', isDark ? 'none' : 'visible');
    }
    if (map.getLayer('carto-dark-layer')) {
      map.setLayoutProperty('carto-dark-layer', 'visibility', isDark ? 'visible' : 'none');
    }

    if (map.getLayer('ne-states-fill')) {
      if (layerMode === 'risk') {
        map.setPaintProperty('ne-states-fill', 'fill-color', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          '#228B22',
          ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
          ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
          ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
          '#228B22',
        ]);
        map.setPaintProperty('ne-states-fill', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.7,
          0.4,
        ]);
      } else {
        // Natural paper cartographic layer mode
        map.setPaintProperty('ne-states-fill', 'fill-color', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          isDark ? '#1E3A8A' : '#71856B', // hover
          isDark ? '#0B0D17' : '#E8E6DC', // default
        ]);
        map.setPaintProperty('ne-states-fill', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.5,
          0.25,
        ]);
      }
    }
  }, [layerMode, isDark]);

  // Fly camera to selection
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (selectedStation) {
      map.flyTo({
        center: [selectedStation.lng, selectedStation.lat],
        zoom: 8.5,
        pitch: 50,
        duration: 1200,
      });
    } else if (selectedState) {
      map.flyTo({
        center: [selectedState.center[1], selectedState.center[0]],
        zoom: 7.5,
        pitch: 52,
        duration: 1400,
      });
    }
  }, [selectedState, selectedStation]);

  return (
    <div
      ref={mapContainerRef}
      className="absolute inset-0 w-full h-full bg-main"
    />
  );
};
