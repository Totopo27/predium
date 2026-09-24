import React, { useState, useEffect } from 'react';
import { MapView } from './components/Map';
import { Sidebar } from './components/Sidebar';
import { PropertyDetail } from './components/PropertyDetail';
import type { Remate, BienAdjudicado, TerritorioInfo } from './types';
import { reproyectarGeoJson } from './lib/geo';

interface Notificacion {
  tipo: 'info' | 'success' | 'warning';
  mensaje: string;
}

export const App: React.FC = () => {
  const [territorios, setTerritorios] = useState<TerritorioInfo[]>([]);
  const [cantonActivo, setCantonActivo] = useState('Zarcero');
  const [remates, setRemates] = useState<Remate[]>([]);
  const [adjudicados, setAdjudicados] = useState<BienAdjudicado[]>([]);
  const [rematesGeoJson, setRematesGeoJson] = useState<any>(null);
  const [vaciosGeoJson, setVaciosGeoJson] = useState<any>(null);
  const [predioBuscadoGeoJson, setPredioBuscadoGeoJson] = useState<any>(null);
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [tipoMapa, setTipoMapa] = useState<'satelite' | 'calles'>('satelite');
  const [cargandoVacios, setCargandoVacios] = useState(false);
  const [cargandoRemates, setCargandoRemates] = useState(false);
  const [cargandoBancos, setCargandoBancos] = useState(false);
  const [notificacion, setNotificacion] = useState<Notificacion | null>(null);

  const mostrarNotificacion = (tipo: 'info' | 'success' | 'warning', mensaje: string) => {
    setNotificacion({ tipo, mensaje });
    setTimeout(() => {
      setNotificacion(null);
    }, 5000);
  };

  const cargarRemates = (canton: string = cantonActivo) => {
    fetch(`/api/remates?canton=${encodeURIComponent(canton)}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setRemates(Array.isArray(data) ? data : []))
      .catch((err) => {
        console.error('Error al cargar remates:', err);
        setRemates([]);
      });

    fetch(`/api/remates/geojson?canton=${encodeURIComponent(canton)}`)
      .then((res) => (res.ok ? res.json() : { type: 'FeatureCollection', features: [] }))
      .then((data) => {
        const reproyectado = reproyectarGeoJson(data);
        setRematesGeoJson(reproyectado);
      })
      .catch((err) => {
        console.error('Error al cargar capa de remates:', err);
        setRematesGeoJson({ type: 'FeatureCollection', features: [] });
      });
  };

  const cargarAdjudicados = (canton: string = cantonActivo) => {
    fetch(`/api/adjudicados?canton=${encodeURIComponent(canton)}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setAdjudicados(Array.isArray(data) ? data : []))
      .catch((err) => {
        console.error('Error al cargar adjudicados:', err);
        setAdjudicados([]);
      });
  };

  useEffect(() => {
    fetch('/api/territorios')
      .then((res) => res.json())
      .then((data: TerritorioInfo[]) => {
        if (data && data.length > 0) {
          setTerritorios(data);
        }
      })
      .catch((err) => console.error('Error cargando territorios:', err));

    cargarRemates('Zarcero');
    cargarAdjudicados('Zarcero');
  }, []);

  const handleCambiarCanton = (nuevoCanton: string) => {
    setCantonActivo(nuevoCanton);
    cargarRemates(nuevoCanton);
    cargarAdjudicados(nuevoCanton);
    setVaciosGeoJson({ type: 'FeatureCollection', features: [] });
    setSelectedFeature(null);

    const terr = territorios.find((t) => t.canton === nuevoCanton);
    const centro = terr ? terr.centro_lng_lat : [-84.394, 10.188];
    setPredioBuscadoGeoJson({
      type: 'Feature',
      geometry: {
        type: 'Point',
        coordinates: centro,
      },
    });

    mostrarNotificacion('info', `Territorio activo cambiado a: ${nuevoCanton}.`);
  };

  const handleEscanearBoletin = async (dias: number = 15, fecha?: string) => {
    setCargandoRemates(true);
    try {
      const url = fecha
        ? `/api/remates/escanear?canton=${encodeURIComponent(cantonActivo)}&fecha=${fecha}`
        : `/api/remates/escanear?canton=${encodeURIComponent(cantonActivo)}&dias=${dias}`;

      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      cargarRemates(cantonActivo);

      if (data.nuevos_guardados > 0) {
        mostrarNotificacion(
          'success',
          `¡Se ingresaron ${data.nuevos_guardados} nuevos remates para ${cantonActivo} a la base de datos!`
        );
      } else {
        const detalle = fecha ? `Fecha ${fecha}` : `${data.dias_escaneados || dias} días analizados`;
        mostrarNotificacion(
          'info',
          `Boletín analizado (${detalle}): No hay nuevos remates para ${cantonActivo}.`
        );
      }
    } catch (err) {
      console.error('Error al escanear boletín:', err);
      mostrarNotificacion('warning', 'Error al conectar con el servidor para escanear el Boletín.');
      cargarRemates(cantonActivo);
    } finally {
      setCargandoRemates(false);
    }
  };

  const handleSincronizarBancos = async () => {
    setCargandoBancos(true);
    try {
      const res = await fetch(`/api/adjudicados/sincronizar?canton=${encodeURIComponent(cantonActivo)}`, {
        method: 'POST',
      });
      const data = await res.json();
      cargarAdjudicados(cantonActivo);
      mostrarNotificacion(
        'success',
        `Bancos sincronizados: ${data.total_encontrados} propiedades encontradas (${data.nuevos_guardados} nuevas).`
      );
    } catch (err) {
      console.error('Error sincronizando bancos:', err);
      mostrarNotificacion('warning', 'Error al sincronizar catálogos bancarios.');
    } finally {
      setCargandoBancos(false);
    }
  };

  const handleBuscarFinca = async (fincaOPlano: string) => {
    try {
      const res = await fetch(`/api/catastro/buscar?finca=${encodeURIComponent(fincaOPlano)}&canton=${encodeURIComponent(cantonActivo)}`);
      if (!res.ok) {
        setSelectedFeature({
          properties: {
            tipo: 'PREDIO_NO_DIGITALIZADO',
            finca: fincaOPlano,
            distrito: `No georreferenciado en WFS (${cantonActivo})`,
            detalles: 'Este inmueble no tiene plano digitalizado en el catastro municipal actual o es una finca antigua.',
          },
        });
        mostrarNotificacion('info', `Finca ${fincaOPlano}: No localizada en catastro de ${cantonActivo}.`);
        return;
      }
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setPredioBuscadoGeoJson(reproyectado);
      setSelectedFeature(reproyectado);
      mostrarNotificacion('success', `Predio ${fincaOPlano} localizado en catastro de ${cantonActivo}.`);
    } catch (err) {
      console.error('Error al consultar catastro:', err);
    }
  };

  const handleEjecutarGapAnalysis = async (distrito: string = 'TODOS') => {
    setCargandoVacios(true);
    try {
      const res = await fetch(`/api/vacios/geojson?canton=${encodeURIComponent(cantonActivo)}&distrito=${encodeURIComponent(distrito)}&area_min=200&limite_predios=100`);
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setVaciosGeoJson(reproyectado);
      const total = reproyectado?.features?.length || 0;

      if (total > 0) {
        const primerVacio = reproyectado.features[0];
        setSelectedFeature(primerVacio);
        setPredioBuscadoGeoJson(primerVacio);
        mostrarNotificacion(
          'success',
          `Detección completada: ${total} vacíos detectados en ${distrito === 'TODOS' ? cantonActivo : distrito}.`
        );
      } else {
        mostrarNotificacion('info', `No se detectaron vacíos en ${distrito === 'TODOS' ? cantonActivo : distrito}.`);
      }
    } catch (err) {
      console.error('Error al ejecutar Gap Analysis:', err);
      mostrarNotificacion('warning', 'Error al ejecutar el análisis de vacíos topológicos.');
    } finally {
      setCargandoVacios(false);
    }
  };

  const handleSelectRemate = (r: Remate) => {
    setSelectedFeature({
      properties: {
        tipo: 'REMATE',
        folio_real: r.folio_real,
        expediente: r.expediente,
        acreedor: r.acreedor,
        demandado: r.demandado,
        monto_base: `${r.moneda} ${r.monto_base.toLocaleString()}`,
        distrito: r.distrito,
        plano: r.plano,
        tipo_oportunidad: r.tipo_oportunidad,
        viabilidad_saneamiento: r.viabilidad_saneamiento,
        detalles_bloqueo: r.detalles_bloqueo,
        score_inversion: r.score_inversion,
      },
    });

    const numFinca = r.folio_real.split('-')[1];
    const cantonRemate = r.canton || cantonActivo;
    if (numFinca) {
      fetch(`/api/catastro/buscar?finca=${encodeURIComponent(numFinca)}&canton=${encodeURIComponent(cantonRemate)}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            const reproyectado = reproyectarGeoJson(data);
            setPredioBuscadoGeoJson(reproyectado);
            setSelectedFeature(reproyectado);
          }
        })
        .catch(() => {});
    }
  };

  const handleSelectAdjudicado = (b: BienAdjudicado) => {
    setSelectedFeature({
      properties: {
        tipo: 'ADJUDICADO_BANCARIO',
        folio_real: b.folio_real,
        institucion: b.institucion,
        id_referencia: b.id_referencia,
        precio: `${b.moneda} ${b.precio_actual.toLocaleString()}`,
        precio_original: b.precio_original ? `${b.moneda} ${b.precio_original.toLocaleString()}` : null,
        descuento: b.porcentaje_descuento,
        canton: b.canton,
        distrito: b.distrito,
        tipo_inmueble: b.tipo_inmueble,
        url_publicacion: b.url_publicacion,
      },
    });

    const numFinca = b.folio_real.split('-')[1];
    const cantonBien = b.canton || cantonActivo;
    if (numFinca) {
      fetch(`/api/catastro/buscar?finca=${encodeURIComponent(numFinca)}&canton=${encodeURIComponent(cantonBien)}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            const reproyectado = reproyectarGeoJson(data);
            setPredioBuscadoGeoJson(reproyectado);
            setSelectedFeature(reproyectado);
          }
        })
        .catch(() => {});
    }
  };

  const handleSelectVacio = (vacioFeature: any) => {
    setSelectedFeature(vacioFeature);
    setPredioBuscadoGeoJson(vacioFeature);
  };

  const handleCentrarEnMapa = (feature: any) => {
    setSelectedFeature(feature);
    setPredioBuscadoGeoJson(feature);
  };

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-slate-950 font-sans relative">
      {/* Toast Flotante de Notificaciones */}
      {notificacion && (
        <div
          className={`absolute top-5 left-1/2 -translate-x-1/2 z-30 px-4 py-2.5 rounded-xl border shadow-2xl backdrop-blur-md text-xs font-semibold flex items-center space-x-2 transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
            notificacion.tipo === 'success'
              ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/40 shadow-emerald-500/10'
              : notificacion.tipo === 'warning'
              ? 'bg-rose-950/90 text-rose-300 border-rose-500/40 shadow-rose-500/10'
              : 'bg-slate-900/95 text-cyan-300 border-cyan-500/40 shadow-cyan-500/10'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-current shrink-0"></span>
          <span>{notificacion.mensaje}</span>
        </div>
      )}

      {/* Barra lateral */}
      <Sidebar
        remates={remates}
        adjudicados={adjudicados}
        vaciosFeatures={vaciosGeoJson?.features || []}
        cantonActivo={cantonActivo}
        territorios={territorios}
        onCambiarCanton={handleCambiarCanton}
        onSelectRemate={handleSelectRemate}
        onSelectAdjudicado={handleSelectAdjudicado}
        onSelectVacio={handleSelectVacio}
        onBuscarFinca={handleBuscarFinca}
        onEjecutarGapAnalysis={handleEjecutarGapAnalysis}
        onEscanearBoletin={handleEscanearBoletin}
        onSincronizarBancos={handleSincronizarBancos}
        cargandoRemates={cargandoRemates}
        cargandoVacios={cargandoVacios}
        cargandoBancos={cargandoBancos}
        totalVacios={vaciosGeoJson?.features?.length || 0}
      />

      {/* Mapa interactivo MapLibre */}
      <main className="flex-1 relative h-full">
        <MapView
          rematesGeoJson={rematesGeoJson}
          vaciosGeoJson={vaciosGeoJson}
          predioBuscadoGeoJson={predioBuscadoGeoJson}
          selectedFeature={selectedFeature}
          onSelectFeature={(feat) => setSelectedFeature(feat)}
          tipoMapa={tipoMapa}
          onSetTipoMapa={(nuevoTipo) => setTipoMapa(nuevoTipo)}
        />

        {selectedFeature && (
          <PropertyDetail
            featureData={selectedFeature}
            onClose={() => setSelectedFeature(null)}
            onCentrarEnMapa={handleCentrarEnMapa}
          />
        )}
      </main>
    </div>
  );
};

export default App;
