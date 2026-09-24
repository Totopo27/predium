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
  urgencia?: 'PRIMERA' | 'SEGUNDA' | 'TERCERA';
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
