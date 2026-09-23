import React, { useState } from 'react';
import { Search, MapPin, AlertTriangle, Building, Flame, Layers, Sparkles } from 'lucide-react';
import type { Remate } from '../types';

interface SidebarProps {
  remates: Remate[];
  onSelectRemate: (remate: Remate) => void;
  onBuscarFinca: (fincaOPlano: string) => void;
  onEjecutarGapAnalysis: () => void;
  cargandoVacios: boolean;
  totalVacios: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  remates,
  onSelectRemate,
  onBuscarFinca,
  onEjecutarGapAnalysis,
  cargandoVacios,
  totalVacios,
}) => {
  const [terminoBusqueda, setTerminoBusqueda] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (terminoBusqueda.trim()) {
      onBuscarFinca(terminoBusqueda.trim());
    }
  };

  return (
    <aside className="w-96 h-screen bg-slate-950/85 backdrop-blur-xl border-r border-slate-800/80 flex flex-col z-20 shadow-2xl">
      {/* Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Building className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Predium
            </h1>
            <p className="text-[11px] text-slate-400 font-medium flex items-center space-x-1">
              <MapPin className="w-3 h-3 text-slate-500" />
              <span>Zarcero, Alajuela</span>
            </p>
          </div>
        </div>
      </div>

      {/* Buscador Catastral WFS */}
      <form onSubmit={handleSubmit} className="p-4 border-b border-slate-800/80 space-y-2">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
          <Search className="w-3 h-3 text-emerald-400" />
          <span>Consulta Catastral WFS</span>
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={terminoBusqueda}
            onChange={(e) => setTerminoBusqueda(e.target.value)}
            placeholder="Ej: 214978 (Finca o Plano)"
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-emerald-500 text-slate-100 placeholder-slate-500 transition"
          />
          <button
            type="submit"
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-2 rounded-xl text-xs font-semibold shadow-md shadow-emerald-600/20 transition flex items-center space-x-1"
          >
            <span>Buscar</span>
          </button>
        </div>
      </form>

      {/* Acciones Rápidas de Inteligencia */}
      <div className="p-4 border-b border-slate-800/80 space-y-2">
        <button
          onClick={onEjecutarGapAnalysis}
          disabled={cargandoVacios}
          className="w-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 py-2.5 px-3 rounded-xl text-xs font-semibold flex items-center justify-between transition group"
        >
          <div className="flex items-center space-x-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 group-hover:rotate-12 transition" />
            <span>Detectar Vacíos (Gap Analysis)</span>
          </div>
          {totalVacios > 0 && (
            <span className="bg-amber-500/20 text-amber-300 text-[10px] px-2 py-0.5 rounded-full font-bold">
              {totalVacios} hallazgos
            </span>
          )}
        </button>
      </div>

      {/* Lista de Oportunidades Registradas */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
            <Layers className="w-3 h-3 text-cyan-400" />
            <span>Remates Judiciales y Municipales</span>
          </label>
          <span className="text-[10px] bg-slate-800/80 text-slate-400 px-2 py-0.5 rounded-full font-semibold">
            {remates.length}
          </span>
        </div>

        {remates.length === 0 ? (
          <div className="text-center py-8 text-slate-500 space-y-2">
            <AlertTriangle className="w-6 h-6 mx-auto text-slate-600" />
            <p className="text-xs">No hay remates activos en la base de datos local.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {remates.map((r, i) => (
              <div
                key={i}
                onClick={() => onSelectRemate(r)}
                className="p-3 bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-emerald-500/40 rounded-xl cursor-pointer transition shadow-sm group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-xs text-slate-200 group-hover:text-emerald-400 transition flex items-center space-x-1">
                    <MapPin className="w-3 h-3 text-emerald-500" />
                    <span>{r.folio_real}</span>
                  </span>
                  <div className="flex space-x-1">
                    {r.es_morosidad_municipal && (
                      <span className="text-[9px] bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded font-bold border border-amber-500/20">
                        Municipal
                      </span>
                    )}
                    {r.urgencia === 'TERCERA' && (
                      <span className="text-[9px] bg-rose-500/10 text-rose-400 px-1.5 py-0.5 rounded font-bold border border-rose-500/20 flex items-center space-x-0.5">
                        <Flame className="w-2.5 h-2.5" />
                        <span>3° Subasta</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-baseline justify-between mt-1.5">
                  <span className="text-xs font-extrabold text-emerald-400">
                    {r.moneda} {r.monto_base.toLocaleString()}
                  </span>
                  <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
                    {r.distrito || 'Zarcero Centro'}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 truncate mt-1">
                  {r.acreedor || 'Cobro Judicial'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};
