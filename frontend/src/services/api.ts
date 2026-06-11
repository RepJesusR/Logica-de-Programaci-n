import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1",
  headers: {
    "Content-Type": "application/json",
    // La API key se inyecta en build-time via variable de entorno
    ...(import.meta.env.VITE_API_KEY ? { "X-API-Key": import.meta.env.VITE_API_KEY } : {}),
  },
});

// ── Types ──────────────────────────────────────────────────────────────
export type EstadoDocumento = "VIGENTE" | "POR_VENCER" | "VENCIDO" | "SIN_DOCUMENTO";
export type CanalNotificacion = "WHATSAPP" | "EMAIL";

export interface ResumenFlota {
  total: number;
  vigente: number;
  por_vencer: number;
  vencido: number;
  sin_documento: number;
}

export interface Conductor {
  id: string;
  nro_documento: string;
  nombre: string | null;
  apellido: string | null;
  email: string | null;
  telefono: string | null;
  ultimo_sync: string | null;
}

export interface Documento {
  id: string;
  conductor_id: string;
  tipo_documento_nombre: string;
  fecha_vencimiento: string | null;
  dias_preaviso: number;
  estado: EstadoDocumento;
  dias_para_vencer: number | null;
  ultimo_sync: string | null;
}

// ── API calls ──────────────────────────────────────────────────────────
export const getResumenFlota = (slug: string) =>
  api.get<ResumenFlota>(`/dashboard/${slug}/resumen`).then((r) => r.data);

export const getConductoresCriticos = (slug: string) =>
  api.get<Conductor[]>(`/dashboard/${slug}/criticos`).then((r) => r.data);

export const getConductores = (slug: string, search?: string) =>
  api
    .get<Conductor[]>(`/conductores/${slug}`, { params: search ? { search } : {} })
    .then((r) => r.data);

export const getDocumentosPorEstado = (slug: string, estado?: EstadoDocumento) =>
  api
    .get<Documento[]>(`/documentos/${slug}`, { params: estado ? { estado } : {} })
    .then((r) => r.data);

export const getDocumentosConductor = (slug: string, conductorId: string) =>
  api
    .get<Documento[]>(`/documentos/${slug}/conductor/${conductorId}`)
    .then((r) => r.data);

export const triggerSync = (slug: string) =>
  api.post(`/sync/${slug}/documentos`).then((r) => r.data);

export const triggerNotificaciones = (slug: string) =>
  api.post(`/sync/${slug}/notificaciones`).then((r) => r.data);
