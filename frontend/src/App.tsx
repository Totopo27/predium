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
        alert('Predio no encontrado en el catastro digital de Zarcero.');
        return;
      }
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setPredioBuscadoGeoJson(reproyectado);
      setSelectedFeature(reproyectado);
    } catch (err) {
      alert('Error al consultar el servicio catastral.');
    }
  };

  const handleEjecutarGapAnalysis = async () => {
    setCargandoVacios(true);
    try {
      const res = await fetch('/api/vacios/geojson?distrito=Guadalupe&area_min=400&limite_predios=80');
      const data = await res.json();
      const reproyectado = reproyectarGeoJson(data);
      setVaciosGeoJson(reproyectado);
    } catch (err) {
      alert('Error al ejecutar el análisis de vacíos topológicos.');
    } finally {
      setCargandoVacios(false);
    }
  };

  const handleSelectRemate = (r: Remate) => {
    const numFinca = r.folio_real.split('-')[1];
    if (numFinca) {
      handleBuscarFinca(numFinca);
    }
  };

  return (
    <div className="flex w-screen h-screen overflow-hidden bg-slate-950 font-sans">
      <Sidebar
        remates={remates}
        onSelectRemate={handleSelectRemate}
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
