import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import { Compass } from 'lucide-react';

interface MapProps {
  rematesGeoJson: any;
  vaciosGeoJson: any;
  predioBuscadoGeoJson: any;
  onSelectFeature: (feature: any) => void;
  tipoMapa: 'satelite' | 'calles';
  onSetTipoMapa: (tipo: 'satelite' | 'calles') => void;
}

export const MapView: React.FC<MapProps> = ({
  rematesGeoJson,
  vaciosGeoJson,
  predioBuscadoGeoJson,
  onSelectFeature,
  tipoMapa,
  onSetTipoMapa,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  // Función segura para volar a coordenadas válidas de Costa Rica
  const centrarEnCoords = (coordsGeoJson: any) => {
    const map = mapRef.current;
    if (!map || !coordsGeoJson) return;

    const bounds = new maplibregl.LngLatBounds();
    let puntosValidos = 0;

    const recorrer = (c: any) => {
      if (typeof c[0] === 'number') {
        const lon = c[0];
        const lat = c[1];
        // Rango geográfico estricto de Costa Rica en WGS84
        if (lon >= -87.0 && lon <= -82.0 && lat >= 7.5 && lat <= 12.0) {
          bounds.extend([lon, lat]);
          puntosValidos++;
        }
      } else if (Array.isArray(c)) {
        c.forEach(recorrer);
      }
    };

    recorrer(coordsGeoJson);

    if (puntosValidos > 0 && !bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 90, maxZoom: 17, duration: 1200 });
    }
  };

  // Función para alternar capas base de satélite y calles
  const cambiarCapaBase = (tipo: 'satelite' | 'calles') => {
    const map = mapRef.current;
    if (!map) return;
    try {
      if (map.getLayer('capa-satelite')) {
        map.setLayoutProperty('capa-satelite', 'visibility', tipo === 'satelite' ? 'visible' : 'none');
      }
      if (map.getLayer('capa-calles')) {
        map.setLayoutProperty('capa-calles', 'visibility', tipo === 'calles' ? 'visible' : 'none');
      }
    } catch (err) {
      console.warn('Error alternando capas base:', err);
    }
  };

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
          'fill-opacity': 0.5,
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
          'fill-opacity': 0.45,
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

  // Observador de tipoMapa con aplicación inmediata
  useEffect(() => {
    cambiarCapaBase(tipoMapa);
  }, [tipoMapa]);

  // Actualizar datos de remates
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    try {
      const src = map.getSource('remates-source') as maplibregl.GeoJSONSource;
      if (src && rematesGeoJson) {
        src.setData(rematesGeoJson);
      }
    } catch (e) {}
  }, [rematesGeoJson]);

  // Actualizar datos de vacíos y volar automáticamente
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    try {
      const src = map.getSource('vacios-source') as maplibregl.GeoJSONSource;
      if (src && vaciosGeoJson) {
        src.setData(vaciosGeoJson);
        const features = vaciosGeoJson.features;
        if (features && features.length > 0 && features[0].geometry) {
          centrarEnCoords(features[0].geometry.coordinates);
        }
      }
    } catch (e) {}
  }, [vaciosGeoJson]);

  // Actualizar y volar al predio buscado / seleccionado
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    try {
      const src = map.getSource('predio-buscado-source') as maplibregl.GeoJSONSource;
      if (src && predioBuscadoGeoJson) {
        src.setData(predioBuscadoGeoJson);
        const coords = predioBuscadoGeoJson.geometry?.coordinates;
        if (coords) {
          centrarEnCoords(coords);
        }
      }
    } catch (e) {}
  }, [predioBuscadoGeoJson]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Controles flotantes de capas y perspectiva */}
      <div className="absolute top-5 left-5 z-10 flex space-x-2">
        {/* Toggle Satélite | Calles con acción directa */}
        <div className="flex bg-slate-900/90 rounded-xl border border-slate-700/80 p-0.5 shadow-xl backdrop-blur-md">
          <button
            onClick={() => {
              onSetTipoMapa('satelite');
              cambiarCapaBase('satelite');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              tipoMapa === 'satelite'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Satélite
          </button>
          <button
            onClick={() => {
              onSetTipoMapa('calles');
              cambiarCapaBase('calles');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              tipoMapa === 'calles'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Calles
          </button>
        </div>

        {/* Botón de alternar inclinación 2.5D */}
        <button
          onClick={() => {
            const map = mapRef.current;
            if (map) {
              const currentPitch = map.getPitch();
              map.easeTo({ pitch: currentPitch > 10 ? 0 : 55, duration: 800 });
            }
          }}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900/90 hover:bg-slate-800 text-slate-100 rounded-xl border border-slate-700/80 shadow-xl backdrop-blur-md text-xs font-semibold transition"
        >
          <Compass className="w-3.5 h-3.5 text-emerald-400" />
          <span>Vista 2.5D</span>
        </button>
      </div>
    </div>
  );
};
