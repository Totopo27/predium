import React, { useState, useEffect } from 'react';
import { MapView } from './components/Map';
import { Sidebar } from './components/Sidebar';
import { PropertyDetail } from './components/PropertyDetail';
import type { Remate } from './types';
import { reproyectarGeoJson } from './lib/geo';

export const App: React.FC = () => {
  const [remates, setRemates] = useState<Remate[]>([]);
  const [rematesGeoJson, setRematesGeoJson] = useState<any>(null);
  const [vaciosGeoJson, setVaciosGeoJson] = useState<any>(null);
  const [predioBuscadoGeoJson, setPredioBuscadoGeoJson] = useState<any>(null);
  const [selectedFeature, setSelectedFeature] = useState<any>(null);
  const [tipoMapa, setTipoMapa] = useState<'satelite' | 'calles'>('satelite');
  const [cargandoVacios, setCargandoVacios] = useState(false);

  useEffect(() => {
    fetch('/api/remates?canton=Zarcero')
      .then((res) => res.json())
      .then((data) => setRemates(data))
      .catch((err) => console.error('Error al cargar remates:', err));

    fetch('/api/remates/geojson?canton=Zarcero')
      .then((res) => res.json())
      .then((data) => {
        const reproyectado = reproyectarGeoJson(data);
        setRematesGeoJson(reproyectado);
      })
      .catch((err) => console.error('Error al cargar capa de remates:', err));
  }, []);

  const handleBuscarFinca = async (fincaOPlano: string) => {
    try {
      const res = await fetch(`/api/catastro/buscar?finca=${fincaOPlano}`);
      if (!res.ok) {
        // En lugar de alert bloqueante, mostrar ficha vacía con aviso
        setSelectedFeature({
          properties: {
            tipo: 'PREDIO_NO_DIGITALIZADO',
            finca: fincaOPlano,
            distrito: 'No georreferenciado en WFS digital',
            detalles: 'Este inmueble no tiene plano digitalizado en el catastro municipal actual o es una finca antigua.',
          },
        });
        return;
      }
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setPredioBuscadoGeoJson(reproyectado);
      setSelectedFeature(reproyectado);
    } catch (err) {
      console.error('Error al consultar catastro:', err);
    }
  };

  const handleEjecutarGapAnalysis = async () => {
    setCargandoVacios(true);
    try {
      const res = await fetch('/api/vacios/geojson?distrito=Guadalupe&area_min=400&limite_predios=80');
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setVaciosGeoJson(reproyectado);
      if (reproyectado?.features && reproyectado.features.length > 0) {
        setSelectedFeature(reproyectado.features[0]);
      }
    } catch (err) {
      console.error('Error al ejecutar Gap Analysis:', err);
    } finally {
      setCargandoVacios(false);
    }
  };

  const handleSelectRemate = (r: Remate) => {
    // 1. Mostrar de inmediato la ficha con la información legal del remate
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
      },
    });

    // 2. Si tiene número de finca, intentar volar a su polígono en el catastro si existe
    const numFinca = r.folio_real.split('-')[1];
    if (numFinca) {
      fetch(`/api/catastro/buscar?finca=${numFinca}`)
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

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-slate-950 font-sans">
      <Sidebar
        remates={remates}
        vaciosFeatures={vaciosGeoJson?.features || []}
        onSelectRemate={handleSelectRemate}
        onSelectVacio={handleSelectVacio}
        onBuscarFinca={handleBuscarFinca}
        onEjecutarGapAnalysis={handleEjecutarGapAnalysis}
        cargandoVacios={cargandoVacios}
        totalVacios={vaciosGeoJson?.features?.length || 0}
      />

      <main className="flex-1 relative h-full">
        <MapView
          rematesGeoJson={rematesGeoJson}
          vaciosGeoJson={vaciosGeoJson}
          predioBuscadoGeoJson={predioBuscadoGeoJson}
          onSelectFeature={(feat) => setSelectedFeature(feat)}
          tipoMapa={tipoMapa}
          onToggleTipoMapa={() => setTipoMapa(tipoMapa === 'satelite' ? 'calles' : 'satelite')}
        />

        {selectedFeature && (
          <PropertyDetail
            featureData={selectedFeature}
            onClose={() => setSelectedFeature(null)}
          />
        )}
      </main>
    </div>
  );
};

export default App;
