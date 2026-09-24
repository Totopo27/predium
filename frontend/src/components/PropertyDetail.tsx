import React, { useState, useEffect } from 'react';
import { X, Scale, ShieldAlert, CheckCircle2, LocateFixed, HelpCircle, Landmark, ExternalLink, Percent } from 'lucide-react';
import type { DiagnosticoPatrimonial } from '../types';

interface PropertyDetailProps {
  featureData: any;
  onClose: () => void;
  onCentrarEnMapa: (feature: any) => void;
}

export const PropertyDetail: React.FC<PropertyDetailProps> = ({
  featureData,
  onClose,
  onCentrarEnMapa,
}) => {
  const [diagnostico, setDiagnostico] = useState<DiagnosticoPatrimonial | null>(null);
  const [cargandoDiag, setCargandoDiag] = useState(false);

  // Reiniciar estado de diagnóstico cuando cambia la propiedad seleccionada
  useEffect(() => {
    setDiagnostico(null);
  }, [featureData]);

  const props = featureData?.properties || {};
  const esRemate = props.tipo === 'REMATE';
  const esVacio = props.tipo === 'VACIO_CATASTRAL';
  const esAdjudicado = props.tipo === 'ADJUDICADO_BANCARIO';
  const noDigitalizado = props.tipo === 'PREDIO_NO_DIGITALIZADO';
  const folio = props.folio_real || (props.finca ? `2-${props.finca}-000` : null);

  const ejecutarDiagnostico = async () => {
    if (!folio) return;
    setCargandoDiag(true);
    try {
      const res = await fetch(`/api/diagnostico?folio=${encodeURIComponent(folio)}`);
      const data = await res.json();
      setDiagnostico(data);
    } catch (err) {
      console.error(err);
    } finally {
      setCargandoDiag(false);
    }
  };

  return (
    <div className="absolute top-5 right-5 w-96 bg-slate-950/90 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-5 z-20 shadow-2xl space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <span className={`text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded border ${
            esVacio
              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              : esAdjudicado
              ? 'bg-purple-500/15 text-purple-300 border-purple-500/30'
              : esRemate
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
          }`}>
            {esVacio ? 'Vacío Catastral' : esAdjudicado ? `Adjudicado (${props.institucion})` : esRemate ? 'Edicto de Remate' : noDigitalizado ? 'Predio Registral' : 'Predio Catastrado'}
          </span>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            {esVacio ? props.id_vacio : folio || props.finca || 'Inmueble'}
          </h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800/50 transition"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Contenido según tipo */}
      <div className="space-y-2 text-xs text-slate-300">
        {esVacio ? (
          <div className="space-y-3">
            <div className="p-3 bg-amber-500/5 rounded-xl border border-amber-500/20 space-y-1.5">
              <div className="flex justify-between items-baseline">
                <span className="text-slate-400">Área Estimada:</span>
                <span className="font-extrabold text-amber-300 text-sm">{Number(props.area_m2).toLocaleString()} m²</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-slate-400">Distrito:</span>
                <span className="font-semibold text-slate-200">{props.distrito}</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-slate-400">Perímetro:</span>
                <span className="font-semibold text-slate-200">{props.perimetro_m} m</span>
              </div>
              <div className="pt-1.5 border-t border-amber-500/10 text-[11px]">
                <span className="text-slate-400 block mb-0.5">Fincas Registradas Colindantes:</span>
                <span className="text-slate-300 font-mono text-[10px]">{props.colindantes || 'Límites de zona'}</span>
              </div>
            </div>

            <div className="p-2.5 bg-slate-900/80 rounded-xl border border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
              <HelpCircle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
              <span>Terreno no incorporado al mosaico catastral digital. Representa un inmueble sin titular aparente, posesión histórica o finca no georreferenciada susceptible de saneamiento.</span>
            </div>

            <button
              onClick={() => onCentrarEnMapa(featureData)}
              className="w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-2 px-3 rounded-xl text-xs flex items-center justify-center space-x-1.5 shadow-md shadow-amber-600/20 transition"
            >
              <LocateFixed className="w-3.5 h-3.5" />
              <span>Ver Vacío en el Mapa</span>
            </button>
          </div>
        ) : esAdjudicado ? (
          <div className="space-y-2.5">
            <div className="p-3 bg-purple-950/20 rounded-xl border border-purple-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-purple-300 font-bold flex items-center space-x-1.5">
                  <Landmark className="w-3.5 h-3.5" />
                  <span>{props.institucion}</span>
                </span>
                {props.descuento > 0 && (
                  <span className="bg-emerald-500/20 text-emerald-300 text-[10px] px-2 py-0.5 rounded-full font-bold border border-emerald-500/30 flex items-center space-x-0.5">
                    <Percent className="w-2.5 h-2.5" />
                    <span>{props.descuento}% Descuento</span>
                  </span>
                )}
              </div>

              <div className="pt-1 border-t border-purple-500/20">
                <span className="text-slate-400 block text-[10px]">Precio de Liquidación Actual</span>
                <span className="font-extrabold text-base text-emerald-400">{props.precio}</span>
                {props.precio_original && (
                  <span className="text-slate-500 line-through text-[11px] block">{props.precio_original}</span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-1.5 pt-1 text-[11px]">
                <div><span className="text-slate-500">Tipo:</span> {props.tipo_inmueble || 'Lote'}</div>
                <div><span className="text-slate-500">Cantón:</span> {props.canton}</div>
                <div><span className="text-slate-500">Ref:</span> {props.id_referencia}</div>
                <div><span className="text-slate-500">Financiamiento:</span> 100%</div>
              </div>
            </div>

            {/* Si ya tenemos el polígono catastral vinculado */}
            {props.area_registro_m2 && (
              <div className="grid grid-cols-2 gap-2 p-2.5 bg-slate-900/60 rounded-xl border border-slate-800 text-[11px]">
                <div><span className="text-slate-500">Área Catastral:</span> {props.area_registro_m2} m²</div>
                <div><span className="text-slate-500">Construcciones:</span> {props.construcciones || 0}</div>
              </div>
            )}

            {props.url_publicacion && (
              <a
                href={props.url_publicacion}
                target="_blank"
                rel="noreferrer"
                className="w-full bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold py-2 px-3 rounded-xl text-xs flex items-center justify-center space-x-1.5 transition"
              >
                <span>Ver Publicación Oficial en {props.institucion}</span>
                <ExternalLink className="w-3 h-3 text-slate-400" />
              </a>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 block text-[10px]">Distrito</span>
              <span className="font-semibold text-slate-200">{props.distrito || 'Zarcero'}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Plano</span>
              <span className="font-semibold text-slate-200">{props.plano || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Área</span>
              <span className="font-semibold text-slate-200">{props.area_registro_m2 || props.area_m2 || 'N/A'} m²</span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">Construcciones</span>
              <span className="font-semibold text-slate-200">{props.construcciones || 0}</span>
            </div>
            {props.monto_base && (
              <div className="col-span-2 pt-2 border-t border-slate-800">
                <span className="text-slate-500 block text-[10px]">Base de Remate</span>
                <span className="font-extrabold text-sm text-emerald-400">{props.monto_base}</span>
              </div>
            )}
            {props.acreedor && (
              <div className="col-span-2 text-[11px] text-slate-400">
                <span className="text-slate-500 block text-[10px]">Acreedor</span>
                <span className="text-slate-200 truncate block">{props.acreedor}</span>
              </div>
            )}
            {props.expediente && (
              <div className="col-span-2 text-[11px] text-slate-400">
                <span className="text-slate-500 block text-[10px]">Expediente Judicial</span>
                <span className="font-mono text-slate-300">{props.expediente}</span>
              </div>
            )}
            {props.tipo_oportunidad && (
              <div className="col-span-2 pt-2 border-t border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500 text-[10px]">Evaluación de Sistema 1:</span>
                  {props.score_inversion && (
                    <span className="text-[10px] font-bold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      Score: {props.score_inversion}/5
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Tipología de Oportunidad:</span>
                  <span className="font-semibold text-emerald-400">{props.tipo_oportunidad}</span>
                </div>
                {props.viabilidad_saneamiento && (
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Viabilidad Saneamiento:</span>
                    <span className={`font-semibold ${props.viabilidad_saneamiento === 'ALTA' ? 'text-emerald-400' : props.viabilidad_saneamiento === 'MEDIA' ? 'text-amber-400' : 'text-rose-400'}`}>
                      {props.viabilidad_saneamiento}
                    </span>
                  </div>
                )}
                {props.detalles_bloqueo && (
                  <p className="text-[10px] text-rose-300 bg-rose-500/10 p-1.5 rounded border border-rose-500/20 mt-1">
                    ⚠ {props.detalles_bloqueo}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Botón de Saneamiento Patrimonial */}
      {!esVacio && folio && (
        <div className="pt-2">
          <button
            onClick={ejecutarDiagnostico}
            disabled={cargandoDiag}
            className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-2 px-3 rounded-xl shadow-lg shadow-emerald-600/20 text-xs flex items-center justify-center space-x-2 transition"
          >
            <Scale className="w-3.5 h-3.5" />
            <span>{cargandoDiag ? 'Consultando RNP...' : 'Analizar Saneamiento Patrimonial'}</span>
          </button>
        </div>
      )}

      {/* Resultado de Diagnóstico Jurídico */}
      {diagnostico && (
        <div className="p-3.5 bg-slate-900/90 rounded-xl border border-slate-700/80 text-xs space-y-2">
          <div className="flex items-center space-x-1.5 text-emerald-400 font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{diagnostico.estrategia_sugerida}</span>
          </div>

          <div className="text-[11px] text-slate-300 space-y-1">
            <p><span className="text-slate-500">Titular:</span> {diagnostico.titular}</p>
            {diagnostico.alerta_sociedad_disuelta && (
              <div className="flex items-center space-x-1 text-rose-400 font-semibold bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                <ShieldAlert className="w-3 h-3" />
                <span>Sociedad Disuelta (Ley 9428)</span>
              </div>
            )}
            <p className="text-slate-400 pt-1 border-t border-slate-800 text-[10px] leading-relaxed">
              {diagnostico.dictamen}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
