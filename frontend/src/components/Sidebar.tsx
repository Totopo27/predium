import React, { useState } from 'react';
import { Search, MapPin, AlertTriangle, Building, Flame, Layers, Sparkles, HelpCircle, Eye, RefreshCw, Clock, ChevronDown, Landmark, Percent, EyeOff } from 'lucide-react';
import type { Remate, BienAdjudicado, FincaInvisible, TerritorioInfo, PobladoInfo } from '../types';

interface SidebarProps {
  remates: Remate[];
  adjudicados: BienAdjudicado[];
  invisibles: FincaInvisible[];
  vaciosFeatures: any[];
  cantonActivo: string;
  territorios: TerritorioInfo[];
  onCambiarCanton: (canton: string) => void;
  onSelectRemate: (remate: Remate) => void;
  onSelectAdjudicado: (bien: BienAdjudicado) => void;
  onSelectInvisible: (finca: FincaInvisible) => void;
  onSelectVacio: (vacioFeature: any) => void;
  onBuscarFinca: (fincaOPlano: string) => void;
  onEjecutarGapAnalysis: (distrito: string) => void;
  onEscanearBoletin: (dias: number, fecha?: string) => void;
  onSincronizarBancos: () => void;
  cargandoRemates: boolean;
  cargandoVacios: boolean;
  cargandoBancos: boolean;
  totalVacios: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  remates,
  adjudicados,
  invisibles,
  vaciosFeatures,
  cantonActivo,
  territorios,
  onCambiarCanton,
  onSelectRemate,
  onSelectAdjudicado,
  onSelectInvisible,
  onSelectVacio,
  onBuscarFinca,
  onEjecutarGapAnalysis,
  onEscanearBoletin,
  onSincronizarBancos,
  cargandoRemates,
  cargandoVacios,
  cargandoBancos,
  totalVacios,
}) => {
  const [terminoBusqueda, setTerminoBusqueda] = useState('');
  const [filtroGeneral, setFiltroGeneral] = useState('');
  const [distritoSeleccionado, setDistritoSeleccionado] = useState('TODOS');
  const [tabOportunidades, setTabOportunidades] = useState<'remates' | 'bancos' | 'invisibles'>('remates');

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
    if (!filtroGeneral.trim()) return true;
    const q = filtroGeneral.toLowerCase();
    return (
      r.folio_real.toLowerCase().includes(q) ||
      (r.acreedor && r.acreedor.toLowerCase().includes(q)) ||
      (r.distrito && r.distrito.toLowerCase().includes(q)) ||
      (r.plano && r.plano.toLowerCase().includes(q))
    );
  });

  const adjudicadosFiltrados = adjudicados.filter((b) => {
    if (!filtroGeneral.trim()) return true;
    const q = filtroGeneral.toLowerCase();
    return (
      b.folio_real.toLowerCase().includes(q) ||
      b.institucion.toLowerCase().includes(q) ||
      b.id_referencia.toLowerCase().includes(q) ||
      (b.distrito && b.distrito.toLowerCase().includes(q))
    );
  });

  const invisiblesFiltrados = invisibles.filter((f) => {
    if (!filtroGeneral.trim()) return true;
    const q = filtroGeneral.toLowerCase();
    return (
      f.folio_real.toLowerCase().includes(q) ||
      f.origen.toLowerCase().includes(q) ||
      f.tipo_oportunidad.toLowerCase().includes(q)
    );
  });

  const territorioActual = territorios.find((t) => t.canton === cantonActivo);
  const distritosDisponibles = territorioActual?.distritos || [];
  const pobladosDisponibles = territorioActual?.poblados || [];

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
            placeholder="Ej: 538150 (Finca o Plano)"
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

      {/* Acciones Rápidas: Detectar Vacíos & Escanear */}
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
              <optgroup label="Distritos Oficiales" className="bg-slate-950 font-bold text-slate-400">
                {distritosDisponibles.map((d) => (
                  <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">
                    {d.label}
                  </option>
                ))}
              </optgroup>
              {pobladosDisponibles.length > 0 && (
                <optgroup label="Caseríos y Sectores" className="bg-slate-950 font-bold text-amber-400">
                  {pobladosDisponibles.map((p: PobladoInfo) => (
                    <option key={p.id} value={p.id} className="bg-slate-900 text-slate-200">
                      {p.label}
                    </option>
                  ))}
                </optgroup>
              )}
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

        {/* BLOQUE ESCANEO BOLETÍN & BANCOS */}
        <div className="space-y-1.5 pt-1 border-t border-slate-800/60">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ingesta de Oportunidades</span>
            <button
              onClick={() => setMostrarConfigEscaneo(!mostrarConfigEscaneo)}
              className="text-[10px] text-cyan-400 hover:text-cyan-300 underline font-medium"
            >
              {mostrarConfigEscaneo ? 'Ocultar' : 'Ajustar periodo'}
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
                    <span>Días atrás:</span>
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
                  </select>
                </div>
              ) : (
                <div className="space-y-1">
                  <input
                    type="date"
                    value={fechaHistorica}
                    onChange={(e) => setFechaHistorica(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-1.5">
            <button
              onClick={handleLanzarEscaneo}
              disabled={cargandoRemates}
              className="bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition"
            >
              <RefreshCw className={`w-3 h-3 text-cyan-400 ${cargandoRemates ? 'animate-spin' : ''}`} />
              <span className="truncate">Escanear Boletín</span>
            </button>

            <button
              onClick={onSincronizarBancos}
              disabled={cargandoBancos}
              className="bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition"
            >
              <Landmark className={`w-3 h-3 text-purple-400 ${cargandoBancos ? 'animate-pulse' : ''}`} />
              <span className="truncate">{cargandoBancos ? 'Consultando...' : 'Sincronizar Bancos'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Lista con Scroll: Vacíos + Pestañas (Remates / Bancos / No Georreferenciadas) */}
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

        {/* PESTAÑAS TRIPLES: REMATES VS BANCOS VS NO GEORREFERENCIADAS */}
        <div className="space-y-2.5">
          <div className="flex bg-slate-900 p-0.5 rounded-xl border border-slate-800 text-[10px] font-bold">
            <button
              onClick={() => setTabOportunidades('remates')}
              className={`flex-1 py-1.5 rounded-lg transition flex items-center justify-center space-x-1 ${
                tabOportunidades === 'remates' ? 'bg-cyan-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3 h-3" />
              <span>Remates ({rematesFiltrados.length})</span>
            </button>
            <button
              onClick={() => setTabOportunidades('bancos')}
              className={`flex-1 py-1.5 rounded-lg transition flex items-center justify-center space-x-1 ${
                tabOportunidades === 'bancos' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Landmark className="w-3 h-3" />
              <span>Bancos ({adjudicadosFiltrados.length})</span>
            </button>
            <button
              onClick={() => setTabOportunidades('invisibles')}
              className={`flex-1 py-1.5 rounded-lg transition flex items-center justify-center space-x-1 ${
                tabOportunidades === 'invisibles' ? 'bg-amber-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <EyeOff className="w-3 h-3" />
              <span>Invisibles ({invisiblesFiltrados.length})</span>
            </button>
          </div>

          {/* Filtro general */}
          <div className="relative">
            <input
              type="text"
              value={filtroGeneral}
              onChange={(e) => setFiltroGeneral(e.target.value)}
              placeholder="Filtrar por folio, banco o distrito..."
              className="w-full bg-slate-900/60 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] focus:outline-none focus:border-cyan-500 text-slate-200 placeholder-slate-500"
            />
          </div>

          {/* Subtítulo explicativo del inventario activo */}
          <div className="flex items-center justify-between px-1 text-[10px] text-slate-400 font-medium">
            {tabOportunidades === 'remates' && (
              <span>Inventario guardado en BD ({rematesFiltrados.length} remates)</span>
            )}
            {tabOportunidades === 'bancos' && (
              <span className="text-purple-300">Inventario bancario en BD ({adjudicadosFiltrados.length} propiedades)</span>
            )}
            {tabOportunidades === 'invisibles' && (
              <span className="text-amber-300">Fincas sin polígono en mapa WFS ({invisiblesFiltrados.length})</span>
            )}
          </div>

          {/* CONTENIDO PESTAÑA REMATES */}
          {tabOportunidades === 'remates' && (
            rematesFiltrados.length === 0 ? (
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
                        {r.score_inversion && r.score_inversion >= 4 && (
                          <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded font-bold border border-emerald-500/30">
                            ★ {r.score_inversion}/5
                          </span>
                        )}
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
            )
          )}

          {/* CONTENIDO PESTAÑA BANCOS */}
          {tabOportunidades === 'bancos' && (
            adjudicadosFiltrados.length === 0 ? (
              <div className="text-center py-6 text-slate-500 space-y-2">
                <Landmark className="w-5 h-5 mx-auto text-slate-600" />
                <p className="text-xs">No hay bienes bancarios para {cantonActivo}.<br/>Tocá 'Sincronizar Bancos' arriba.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {adjudicadosFiltrados.map((b, i) => (
                  <div
                    key={i}
                    onClick={() => onSelectAdjudicado(b)}
                    className="p-3 bg-purple-950/20 hover:bg-purple-950/30 border border-purple-500/30 hover:border-purple-400/60 rounded-xl cursor-pointer transition shadow-sm group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-purple-300 group-hover:text-purple-200 transition flex items-center space-x-1">
                        <MapPin className="w-3 h-3 text-purple-400" />
                        <span>{b.folio_real}</span>
                      </span>
                      <div className="flex items-center space-x-1">
                        <span className="text-[9px] bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded font-bold border border-purple-500/30">
                          {b.institucion}
                        </span>
                        {b.porcentaje_descuento > 0 && (
                          <span className="text-[9px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded font-bold border border-emerald-500/30 flex items-center space-x-0.5">
                            <Percent className="w-2.5 h-2.5" />
                            <span>{b.porcentaje_descuento}% OFF</span>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-baseline justify-between mt-1.5">
                      <span className="text-xs font-extrabold text-emerald-400">
                        {b.moneda} {b.precio_actual.toLocaleString()}
                      </span>
                      <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
                        {b.distrito || b.canton}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 truncate mt-1">
                      <span className="text-slate-500">Ref:</span> {b.id_referencia} · {b.tipo_inmueble}
                    </p>
                  </div>
                ))}
              </div>
            )
          )}

          {/* CONTENIDO PESTAÑA FINCAS NO GEORREFERENCIADAS (INVISIBLES) */}
          {tabOportunidades === 'invisibles' && (
            invisiblesFiltrados.length === 0 ? (
              <div className="text-center py-6 text-slate-500 space-y-2">
                <EyeOff className="w-5 h-5 mx-auto text-amber-500/60" />
                <p className="text-xs">No hay fincas invisibles registradas en {cantonActivo}.<br/>Probá sincronizar bancos o escanear el boletín.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {invisiblesFiltrados.map((f, i) => (
                  <div
                    key={i}
                    onClick={() => onSelectInvisible(f)}
                    className="p-3 bg-amber-950/20 hover:bg-amber-950/30 border border-amber-500/30 hover:border-amber-400/60 rounded-xl cursor-pointer transition shadow-sm group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-amber-300 group-hover:text-amber-200 transition flex items-center space-x-1">
                        <EyeOff className="w-3 h-3 text-amber-400" />
                        <span>{f.folio_real}</span>
                      </span>
                      <div className="flex items-center space-x-1">
                        <span className="text-[9px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold border border-amber-500/30">
                          ★ {f.score_inversion}/5
                        </span>
                        <span className="text-[9px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-semibold border border-slate-700">
                          {f.viabilidad_saneamiento}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-baseline justify-between mt-1.5">
                      <span className="text-xs font-extrabold text-slate-100">
                        {f.precio_referencia}
                      </span>
                      <span className="text-[10px] text-slate-400 truncate max-w-[130px]">
                        {f.origen}
                      </span>
                    </div>

                    <p className="text-[10px] text-amber-400/80 truncate mt-1">
                      {f.estado_wfs}
                    </p>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </div>
    </aside>
  );
};
