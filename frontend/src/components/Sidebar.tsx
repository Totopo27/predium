import React, { useState } from 'react';
import { Search, MapPin, AlertTriangle, Building, Flame, Layers, Sparkles, HelpCircle, Eye, RefreshCw, Calendar, Clock, ChevronDown } from 'lucide-react';
import type { Remate, TerritorioInfo } from '../types';

interface SidebarProps {
  remates: Remate[];
  vaciosFeatures: any[];
  cantonActivo: string;
  territorios: TerritorioInfo[];
  onCambiarCanton: (canton: string) => void;
  onSelectRemate: (remate: Remate) => void;
  onSelectVacio: (vacioFeature: any) => void;
  onBuscarFinca: (fincaOPlano: string) => void;
  onEjecutarGapAnalysis: (distrito: string) => void;
  onEscanearBoletin: (dias: number, fecha?: string) => void;
  cargandoRemates: boolean;
  cargandoVacios: boolean;
  totalVacios: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  remates,
  vaciosFeatures,
  cantonActivo,
  territorios,
  onCambiarCanton,
  onSelectRemate,
  onSelectVacio,
  onBuscarFinca,
  onEjecutarGapAnalysis,
  onEscanearBoletin,
  cargandoRemates,
  cargandoVacios,
  totalVacios,
}) => {
  const [terminoBusqueda, setTerminoBusqueda] = useState('');
  const [filtroRemates, setFiltroRemates] = useState('');
  const [distritoSeleccionado, setDistritoSeleccionado] = useState('TODOS');

  // Parámetros de Escaneo de Boletín
  const [modoEscaneo, setModoEscaneo] = useState<'dias' | 'fecha'>('dias');
  const [diasEscaneo, setDiasEscaneo] = useState<number>(15);
  const [fechaHistorica, setFechaHistorica] = useState<string>('');
  const [mostrarConfigEscaneo, setMostrarConfigEscaneo] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (terminoBusqueda.trim()) {
      onBuscarFinca(terminoBusqueda.trim());
    }
  };

  const handleLanzarEscaneo = () => {
    if (modoEscaneo === 'fecha' && fechaHistorica) {
      onEscanearBoletin(1, fechaHistorica);
    } else {
      onEscanearBoletin(diasEscaneo);
    }
  };

  const rematesFiltrados = remates.filter((r) => {
    if (!filtroRemates.trim()) return true;
    const q = filtroRemates.toLowerCase();
    return (
      r.folio_real.toLowerCase().includes(q) ||
      (r.acreedor && r.acreedor.toLowerCase().includes(q)) ||
      (r.distrito && r.distrito.toLowerCase().includes(q)) ||
      (r.plano && r.plano.toLowerCase().includes(q))
    );
  });

  const territorioActual = territorios.find((t) => t.canton === cantonActivo);
  const distritosDisponibles = territorioActual?.distritos || [];

  return (
    <aside className="w-96 h-screen bg-slate-950/85 backdrop-blur-xl border-r border-slate-800/80 flex flex-col z-20 shadow-2xl">
      {/* Header con Selector Dinámico de Cantón */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Building className="w-5 h-5 text-slate-950" />
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              Predium
            </h1>
            {/* Selector de Cantón Activo */}
            <div className="flex items-center space-x-1 mt-0.5">
              <MapPin className="w-3 h-3 text-emerald-400 shrink-0" />
              <div className="relative inline-flex items-center">
                <select
                  value={cantonActivo}
                  onChange={(e) => {
                    onCambiarCanton(e.target.value);
                    setDistritoSeleccionado('TODOS');
                  }}
                  className="bg-transparent text-[11px] font-bold text-slate-200 focus:outline-none cursor-pointer hover:text-emerald-300 pr-4 appearance-none"
                >
                  {territorios.map((t) => (
                    <option key={t.canton} value={t.canton} className="bg-slate-900 text-slate-200">
                      {t.canton}, {t.provincia}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-2.5 h-2.5 text-slate-400 pointer-events-none absolute right-0" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Buscador Catastral WFS */}
      <form onSubmit={handleSubmit} className="p-4 border-b border-slate-800/80 space-y-2">
        <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
          <Search className="w-3 h-3 text-emerald-400" />
          <span>Consulta Catastral WFS ({cantonActivo})</span>
        </label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={terminoBusqueda}
            onChange={(e) => setTerminoBusqueda(e.target.value)}
            placeholder="Ej: 313004 (Finca o Plano)"
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

      {/* Acciones Rápidas: Detectar Vacíos & Escanear Boletín */}
      <div className="p-4 border-b border-slate-800/80 space-y-3">
        {/* BLOQUE VACÍOS */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Distrito ({cantonActivo})</label>
            <select
              value={distritoSeleccionado}
              onChange={(e) => setDistritoSeleccionado(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-lg px-2 py-0.5 text-[11px] text-slate-200 focus:outline-none focus:border-amber-400 max-w-[190px] truncate"
            >
              {distritosDisponibles.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => onEjecutarGapAnalysis(distritoSeleccionado)}
            disabled={cargandoVacios}
            className="w-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-between transition group"
          >
            <div className="flex items-center space-x-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 group-hover:rotate-12 transition" />
              <span>{cargandoVacios ? 'Buscando en catastro...' : 'Detectar Vacíos'}</span>
            </div>
            {totalVacios > 0 && (
              <span className="bg-amber-500/20 text-amber-300 text-[10px] px-2 py-0.5 rounded-full font-bold">
                {totalVacios} hallazgos
              </span>
            )}
          </button>
        </div>

        {/* BLOQUE ESCANEO BOLETÍN CON CONFIGURACIÓN */}
        <div className="space-y-1.5 pt-1 border-t border-slate-800/60">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Escaneo de Remates ({cantonActivo})</span>
            <button
              onClick={() => setMostrarConfigEscaneo(!mostrarConfigEscaneo)}
              className="text-[10px] text-cyan-400 hover:text-cyan-300 underline font-medium"
            >
              {mostrarConfigEscaneo ? 'Ocultar opciones' : 'Ajustar periodo / fecha'}
            </button>
          </div>

          {mostrarConfigEscaneo && (
            <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800 space-y-2 text-xs">
              <div className="flex bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-[10px]">
                <button
                  type="button"
                  onClick={() => setModoEscaneo('dias')}
                  className={`flex-1 py-1 rounded font-semibold transition ${
                    modoEscaneo === 'dias' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Días Recientes
                </button>
                <button
                  type="button"
                  onClick={() => setModoEscaneo('fecha')}
                  className={`flex-1 py-1 rounded font-semibold transition ${
                    modoEscaneo === 'fecha' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Fecha Histórica
                </button>
              </div>

              {modoEscaneo === 'dias' ? (
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-[11px] flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>Días hábiles atrás:</span>
                  </span>
                  <select
                    value={diasEscaneo}
                    onChange={(e) => setDiasEscaneo(Number(e.target.value))}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value={5}>5 días</option>
                    <option value={15}>15 días</option>
                    <option value={30}>30 días (1 mes)</option>
                    <option value={60}>60 días (2 meses)</option>
                    <option value={90}>90 días (3 meses)</option>
                  </select>
                </div>
              ) : (
                <div className="space-y-1">
                  <span className="text-slate-400 text-[11px] flex items-center space-x-1">
                    <Calendar className="w-3 h-3 text-slate-500" />
                    <span>Fecha de publicación:</span>
                  </span>
                  <input
                    type="date"
                    value={fechaHistorica}
                    onChange={(e) => setFechaHistorica(e.target.value)}
                    placeholder="YYYY-MM-DD"
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <p className="text-[10px] text-slate-500 italic">Ej: 2023-08-18 para remates de San Ramón.</p>
                </div>
              )}
            </div>
          )}

          <button
            onClick={handleLanzarEscaneo}
            disabled={cargandoRemates}
            className="w-full bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-between transition group"
          >
            <div className="flex items-center space-x-2">
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 transition ${cargandoRemates ? 'animate-spin' : 'group-hover:rotate-45'}`} />
              <span>{cargandoRemates ? 'Escaneando Boletín...' : `Escanear Boletín (${cantonActivo})`}</span>
            </div>
            <span className="bg-cyan-500/20 text-cyan-300 text-[10px] px-2 py-0.5 rounded-full font-bold">
              {rematesFiltrados.length} remates
            </span>
          </button>
        </div>
      </div>

      {/* Lista con Scroll: Vacíos + Remates */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* SECCIÓN VACÍOS DETECTADOS */}
        {vaciosFeatures && vaciosFeatures.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-bold uppercase tracking-wider text-amber-400 flex items-center space-x-1">
                <HelpCircle className="w-3 h-3 text-amber-400" />
                <span>Vacíos Catastrales ({cantonActivo})</span>
              </label>
              <span className="text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full font-bold">
                {vaciosFeatures.length}
              </span>
            </div>

            <div className="space-y-2">
              {vaciosFeatures.map((vf: any, idx: number) => {
                const p = vf.properties || {};
                return (
                  <div
                    key={idx}
                    onClick={() => onSelectVacio(vf)}
                    className="p-3 bg-amber-500/5 hover:bg-amber-500/10 border border-amber-500/30 hover:border-amber-400/60 rounded-xl cursor-pointer transition shadow-sm group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-amber-300 group-hover:text-amber-200 transition">
                        {p.id_vacio || `Vacío #${idx + 1}`}
                      </span>
                      <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold border border-amber-500/30 flex items-center space-x-1">
                        <Eye className="w-2.5 h-2.5" />
                        <span>Ver en mapa</span>
                      </span>
                    </div>
                    <div className="flex items-baseline justify-between mt-1">
                      <span className="text-xs font-extrabold text-slate-100">
                        {Number(p.area_m2 || 0).toLocaleString()} m²
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {p.distrito || cantonActivo}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 truncate mt-1">
                      <span className="text-slate-500">Colinda con:</span> {p.colindantes || 'Límites de zona'}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* SECCIÓN REMATES JUDICIALES Y MUNICIPALES */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
              <Layers className="w-3 h-3 text-cyan-400" />
              <span>Remates ({cantonActivo})</span>
            </label>
            <div className="flex items-center space-x-1.5">
              <button
                onClick={() => onEscanearBoletin(diasEscaneo)}
                disabled={cargandoRemates}
                title="Actualizar lista de remates"
                className="text-slate-400 hover:text-cyan-400 p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${cargandoRemates ? 'animate-spin' : ''}`} />
              </button>
              <span className="text-[10px] bg-slate-800/80 text-slate-400 px-2 py-0.5 rounded-full font-semibold">
                {rematesFiltrados.length}
              </span>
            </div>
          </div>

          {/* Filtro rápido de remates */}
          <div className="relative">
            <input
              type="text"
              value={filtroRemates}
              onChange={(e) => setFiltroRemates(e.target.value)}
              placeholder="Filtrar por acreedor o folio..."
              className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] focus:outline-none focus:border-cyan-500 text-slate-200 placeholder-slate-500"
            />
          </div>

          {rematesFiltrados.length === 0 ? (
            <div className="text-center py-6 text-slate-500 space-y-2">
              <AlertTriangle className="w-5 h-5 mx-auto text-slate-600" />
              <p className="text-xs">No hay remates cargados para {cantonActivo}.<br/>Usá 'Escanear Boletín' arriba.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {rematesFiltrados.map((r, i) => (
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
                      {r.distrito || cantonActivo}
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
      </div>
    </aside>
  );
};
