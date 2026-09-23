import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import { Layers, Compass } from 'lucide-react';

interface MapProps {
  rematesGeoJson: any;
  vaciosGeoJson: any;
  predioBuscadoGeoJson: any;
  onSelectFeature: (feature: any) => void;
  tipoMapa: 'satelite' | 'calles';
  onToggleTipoMapa: () => void;
}

export const MapView: React.FC<MapProps> = ({
  rematesGeoJson,
  vaciosGeoJson,
  predioBuscadoGeoJson,
  onSelectFeature,
  tipoMapa,
  onToggleTipoMapa,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const mapStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        'esri-sat': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '&copy; Esri & contributors',
        },
        'osm-tiles': {
          type: 'raster',
          tiles: [
            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          ],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: 'capa-calles',
          type: 'raster',
          source: 'osm-tiles',
          layout: {
            visibility: tipoMapa === 'calles' ? 'visible' : 'none',
          },
        },
        {
          id: 'capa-satelite',
          type: 'raster',
          source: 'esri-sat',
          layout: {
            visibility: tipoMapa === 'satelite' ? 'visible' : 'none',
          },
        },
      ],
    };

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: mapStyle,
      center: [-84.394, 10.188],
      zoom: 14,
      pitch: 35,
      bearing: 0,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'bottom-right');
    mapRef.current = map;

    map.on('load', () => {
      // 1. Capa de Vacíos Catastrales (Amarillo)
      map.addSource('vacios-source', {
        type: 'geojson',
        data: vaciosGeoJson || { type: 'FeatureCollection', features: [] },
      });

      map.addLayer({
        id: 'vacios-fill',
        type: 'fill',
        source: 'vacios-source',
        paint: {
          'fill-color': '#f59e0b',
          'fill-opacity': 0.45,
        },
      });

      map.addLayer({
        id: 'vacios-line',
        type: 'line',
        source: 'vacios-source',
        paint: {
          'line-color': '#fbbf24',
          'line-width': 2.5,
        },
      });

      // 2. Capa de Remates (Rojo)
      map.addSource('remates-source', {
        type: 'geojson',
        data: rematesGeoJson || { type: 'FeatureCollection', features: [] },
      });

      map.addLayer({
        id: 'remates-fill',
        type: 'fill',
        source: 'remates-source',
        paint: {
          'fill-color': '#f43f5e',
          'fill-opacity': 0.4,
        },
      });

      map.addLayer({
        id: 'remates-line',
        type: 'line',
        source: 'remates-source',
        paint: {
          'line-color': '#fb7185',
          'line-width': 3,
        },
      });

      // 3. Capa de Predio Buscado (Verde Esmeralda)
      map.addSource('predio-buscado-source', {
        type: 'geojson',
        data: predioBuscadoGeoJson || { type: 'FeatureCollection', features: [] },
      });

      map.addLayer({
        id: 'predio-buscado-fill',
        type: 'fill',
        source: 'predio-buscado-source',
        paint: {
          'fill-color': '#10b981',
          'fill-opacity': 0.45,
        },
      });

      map.addLayer({
        id: 'predio-buscado-line',
        type: 'line',
        source: 'predio-buscado-source',
        paint: {
          'line-color': '#34d399',
          'line-width': 3.5,
        },
      });

      ['remates-fill', 'vacios-fill', 'predio-buscado-fill'].forEach((layerId) => {
        map.on('click', layerId, (e: any) => {
          if (e.features && e.features.length > 0) {
            onSelectFeature(e.features[0]);
          }
        });

        map.on('mouseenter', layerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', layerId, () => {
          map.getCanvas().style.cursor = '';
        });
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Conmutador directo de visibilidad entre satélite y calles
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    if (map.getLayer('capa-satelite')) {
      map.setLayoutProperty(
        'capa-satelite',
        'visibility',
        tipoMapa === 'satelite' ? 'visible' : 'none'
      );
    }
    if (map.getLayer('capa-calles')) {
      map.setLayoutProperty(
        'capa-calles',
        'visibility',
        tipoMapa === 'calles' ? 'visible' : 'none'
      );
    }
  }, [tipoMapa]);

  // Actualizar datos de remates
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource('remates-source') as maplibregl.GeoJSONSource;
    if (src && rematesGeoJson) {
      src.setData(rematesGeoJson);
    }
  }, [rematesGeoJson]);

  // Actualizar datos de vacíos y volar automáticamente
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource('vacios-source') as maplibregl.GeoJSONSource;
    if (src && vaciosGeoJson) {
      src.setData(vaciosGeoJson);

      const features = vaciosGeoJson.features;
      if (features && features.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        const recorrer = (c: any) => {
          if (typeof c[0] === 'number') {
            bounds.extend([c[0], c[1]]);
          } else {
            c.forEach(recorrer);
          }
        };
        features.forEach((f: any) => {
          if (f.geometry?.coordinates) recorrer(f.geometry.coordinates);
        });
        map.fitBounds(bounds, { padding: 80, maxZoom: 16, pitch: 45, duration: 1500 });
      }
    }
  }, [vaciosGeoJson]);

  // Actualizar y volar al predio buscado
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const src = map.getSource('predio-buscado-source') as maplibregl.GeoJSONSource;
    if (src && predioBuscadoGeoJson) {
      src.setData(predioBuscadoGeoJson);

      const coords = predioBuscadoGeoJson.geometry?.coordinates;
      if (coords) {
        const bounds = new maplibregl.LngLatBounds();
        const recorrer = (c: any) => {
          if (typeof c[0] === 'number') {
            bounds.extend([c[0], c[1]]);
          } else {
            c.forEach(recorrer);
          }
        };
        recorrer(coords);
        map.fitBounds(bounds, { padding: 80, maxZoom: 18, pitch: 45, duration: 1500 });
      }
    }
  }, [predioBuscadoGeoJson]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Controles flotantes de capas y perspectiva */}
      <div className="absolute top-5 left-5 z-10 flex space-x-2">
        <button
          onClick={onToggleTipoMapa}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900/90 hover:bg-slate-800 text-slate-100 rounded-xl border border-slate-700/80 shadow-xl backdrop-blur-md text-xs font-semibold transition"
        >
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>{tipoMapa === 'satelite' ? 'Ver Calles' : 'Ver Satélite'}</span>
        </button>

        <button
          onClick={() => {
            const map = mapRef.current;
            if (map) {
              const currentPitch = map.getPitch();
              map.easeTo({ pitch: currentPitch > 10 ? 0 : 55, duration: 800 });
            }
          }}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900/90 hover:bg-slate-800 text-slate-100 rounded-xl border border-slate-700/80 shadow-xl backdrop-blur-md text-xs font-semibold transition"
        >
          <Compass className="w-3.5 h-3.5 text-emerald-400" />
          <span>Alternar 2.5D</span>
        </button>
      </div>
    </div>
  );
};
