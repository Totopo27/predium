import React, { useState } from 'react';
import { X, Scale, ShieldAlert, CheckCircle2 } from 'lucide-react';
import type { DiagnosticoPatrimonial } from '../types';

interface PropertyDetailProps {
  featureData: any;
  onClose: () => void;
}

export const PropertyDetail: React.FC<PropertyDetailProps> = ({ featureData, onClose }) => {
  const [diagnostico, setDiagnostico] = useState<DiagnosticoPatrimonial | null>(null);
  const [cargandoDiag, setCargandoDiag] = useState(false);

  const props = featureData?.properties || {};
  const esRemate = props.tipo === 'REMATE';
  const esVacio = props.tipo === 'VACIO_CATASTRAL';
  const folio = props.folio_real || (props.finca ? `2-${props.finca}-000` : null);

  const ejecutarDiagnostico = async () => {
    if (!folio) return;
    setCargandoDiag(true);
    try {
      const res = await fetch(`/api/diagnostico?folio=${folio}&escenario=sociedad_disuelta`);
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
          <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {esVacio ? 'Eslabón Perdido' : esRemate ? 'Edicto de Remate' : 'Predio Catastrado'}
          </span>
          <h2 className="text-base font-bold text-slate-100 mt-1">
            {esVacio ? props.id_vacio : folio || 'Inmueble'}
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
          <div className="space-y-1.5 p-3 bg-slate-900/60 rounded-xl border border-slate-800">
            <p><span className="text-slate-500">Distrito:</span> {props.distrito}</p>
            <p><span className="text-slate-500">Área Estimada:</span> <strong className="text-amber-400">{Number(props.area_m2).toLocaleString()} m²</strong></p>
            <p><span className="text-slate-500">Perímetro:</span> {props.perimetro_m} m</p>
            <p className="text-[11px] text-slate-400 mt-1"><span className="text-slate-500">Fincas Colindantes:</span> {props.colindantes || 'Sin datos'}</p>
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
              <span className="text-slate-500 block text-[10px]">Área Registro</span>
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
