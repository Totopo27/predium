export interface Remate {
  id_edicto?: string;
  folio_real: string;
  plano?: string;
  canton: string;
  distrito?: string;
  expediente?: string;
  acreedor?: string;
  demandado?: string;
  moneda: string;
  monto_base: number;
  monto_segundo?: number;
  monto_tercero?: number;
  fecha_publicacion?: string;
  es_morosidad_municipal?: boolean;
  tipo_oportunidad?: string;
  viabilidad_saneamiento?: 'ALTA' | 'MEDIA' | 'BAJA';
  tiene_gravamen_bloqueante?: boolean;
  detalles_bloqueo?: string;
  urgencia?: 'PRIMERA' | 'SEGUNDA' | 'TERCERA' | 'VENTA_DIRECTA';
  score_inversion?: number;
}

export interface BienAdjudicado {
  id_referencia: string;
  institucion: string;
  folio_real: string;
  plano_catastrado?: string;
  tipo_inmueble: string;
  provincia: string;
  canton: string;
  distrito?: string;
  precio_actual: number;
  precio_original?: number;
  porcentaje_descuento: number;
  moneda: string;
  financiamiento_disponible: boolean;
  url_publicacion?: string;
}

export interface FincaInvisible {
  folio_real: string;
  origen: string;
  tipo_inmueble: string;
  canton: string;
  distrito: string;
  precio_referencia: string;
  descuento: number;
  estado_wfs: string;
  tipo_oportunidad: string;
  viabilidad_saneamiento: string;
  detalles_saneamiento: string;
  score_inversion: number;
  url_publicacion?: string;
  expediente?: string;
  vacio_asociado?: any;
  vecinos_colindantes?: string[];
}

export interface PredioPropiedades {
  finca: string;
  plano?: string;
  distrito: string;
  area_registro_m2?: number;
  area_poligono_m2?: number;
  frente_m?: number;
  fondo_m?: number;
  construcciones: number;
  categoria: string;
  centroide_x: number;
  centroide_y: number;
}

export interface DiagnosticoPatrimonial {
  folio_real: string;
  titular: string;
  cedula: string;
  tipo_titular: 'FISICA' | 'JURIDICA';
  alerta_sociedad_disuelta: boolean;
  alerta_usufructo_activo: boolean;
  alerta_embargos_judiciales: boolean;
  estrategia_sugerida: string;
  dictamen: string;
}

export interface VacioCatastral {
  id_vacio: string;
  distrito: string;
  area_m2: number;
  perimetro_m: number;
  colindantes: string;
}

export interface DistritoInfo {
  id: string;
  label: string;
}

export interface TerritorioInfo {
  canton: string;
  provincia: string;
  codigo_canton: string;
  centro_lng_lat: [number, number];
  distritos: DistritoInfo[];
  proveedor_activo: boolean;
  descripcion_cobertura: string;
}
