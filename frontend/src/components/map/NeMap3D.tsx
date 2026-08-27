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
}

// MapLibre Light Cartographic Style with Warm Paper Topography & DEM Terrain Relief
const WARM_CARTOGRAPHIC_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    'carto-light': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; CartoDB &copy; OpenStreetMap contributors',
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
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const stationMarkersRef = useRef<maplibregl.Marker[]>([]);
  const citizenMarkersRef = useRef<maplibregl.Marker[]>([]);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const hoveredIdRef = useRef<string | number | null>(null);

  // Initialize MapLibre GL JS Map instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: WARM_CARTOGRAPHIC_STYLE,
      center: NE_CENTER,
      zoom: 6.3,
      pitch: 45,
      bearing: -10,
      maxPitch: 85,
      minZoom: 5,
      maxZoom: 13,
      attributionControl: false,
    });

    mapRef.current = map;

    map.on('load', () => {
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
            '#23483A',
            ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
            ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
            ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
            '#23483A',
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
          'line-color': '#23483A',
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
          'line-color': '#23483A',
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
          <div class="px-2 py-1 bg-[#FAF9F3] border border-[#A87C58] rounded-md shadow-md text-[10px] font-mono font-bold text-[#202622] flex items-center space-x-1">
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

  // Update User Location Ring Marker
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !userLocation) return;

    if (!userMarkerRef.current) {
      const el = document.createElement('div');
      el.className = 'relative flex items-center justify-center';
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

  // Update Layer mode paint properties
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('ne-states-fill')) {
      if (layerMode === 'risk') {
        map.setPaintProperty('ne-states-fill', 'fill-color', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          '#23483A',
          ['==', ['get', 'riskLevel'], 'CRITICAL'], '#8E2F2B',
          ['==', ['get', 'riskLevel'], 'HIGH'], '#C6533C',
          ['==', ['get', 'riskLevel'], 'WATCH'], '#D88A32',
          '#23483A',
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
          '#71856B',
          '#E8E6DC',
        ]);
        map.setPaintProperty('ne-states-fill', 'fill-opacity', [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.5,
          0.25,
        ]);
      }
    }
  }, [layerMode]);

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
      className="relative w-full h-[85vh] sm:h-[88vh] min-h-[500px] rounded-2xl overflow-hidden shadow-lg border border-[#C7B89B]/40 bg-[#F4F1E8]"
    />
  );
};
