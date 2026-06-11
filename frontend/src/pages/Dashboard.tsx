import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Bell, Truck, AlertCircle } from "lucide-react";
import {
  getResumenFlota,
  getDocumentosPorEstado,
  getConductores,
  triggerSync,
  triggerNotificaciones,
  type EstadoDocumento,
} from "../services/api";
import { ResumenCards } from "../components/ResumenCards";
import { FlotaTable } from "../components/FlotaTable";

const TENANT_SLUG = import.meta.env.VITE_TENANT_SLUG ?? "piloto";

const FILTROS: { label: string; value: EstadoDocumento | undefined }[] = [
  { label: "Todos", value: undefined },
  { label: "Vencidos", value: "VENCIDO" },
  { label: "Por vencer", value: "POR_VENCER" },
  { label: "Vigentes", value: "VIGENTE" },
];

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm flex items-center gap-2">
      <AlertCircle size={16} className="shrink-0" />
      {message}
    </div>
  );
}

export default function Dashboard() {
  const qc = useQueryClient();
  const [filtro, setFiltro] = useState<EstadoDocumento | undefined>("VENCIDO");
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [notifMsg, setNotifMsg] = useState<string | null>(null);

  const resumenQ = useQuery({
    queryKey: ["resumen", TENANT_SLUG],
    queryFn: () => getResumenFlota(TENANT_SLUG),
    refetchInterval: 60_000,
  });

  const documentosQ = useQuery({
    queryKey: ["documentos", TENANT_SLUG, filtro],
    queryFn: () => getDocumentosPorEstado(TENANT_SLUG, filtro),
  });

  const conductoresQ = useQuery({
    queryKey: ["conductores", TENANT_SLUG],
    queryFn: () => getConductores(TENANT_SLUG),
  });

  const syncMutation = useMutation({
    mutationFn: () => triggerSync(TENANT_SLUG),
    onSuccess: () => {
      setSyncMsg("Sync iniciado — los datos se actualizarán en breve.");
      qc.invalidateQueries({ queryKey: ["resumen"] });
      qc.invalidateQueries({ queryKey: ["documentos"] });
    },
    onError: () => setSyncMsg("Error al iniciar el sync."),
  });

  const notifMutation = useMutation({
    mutationFn: () => triggerNotificaciones(TENANT_SLUG),
    onSuccess: () => setNotifMsg("Notificaciones disparadas en background."),
    onError: () => setNotifMsg("Error al disparar notificaciones."),
  });

  const isLoadingMain = resumenQ.isLoading || conductoresQ.isLoading;
  const hasError = resumenQ.isError || documentosQ.isError;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Truck size={26} />
          <div>
            <h1 className="text-lg font-bold tracking-tight">Zuvra Compliance</h1>
            <p className="text-slate-400 text-xs">Monitor documental · {TENANT_SLUG}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setSyncMsg(null); syncMutation.mutate(); }}
            disabled={syncMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={syncMutation.isPending ? "animate-spin" : ""} />
            Sincronizar
          </button>
          <button
            onClick={() => { setNotifMsg(null); notifMutation.mutate(); }}
            disabled={notifMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm transition-colors disabled:opacity-50"
          >
            <Bell size={14} />
            Notificar
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Error global */}
        {hasError && (
          <ErrorBanner message="Error al cargar datos. Verificá la conexión con la API." />
        )}

        {/* KPI Cards */}
        {isLoadingMain ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 h-24 animate-pulse" />
            ))}
          </div>
        ) : resumenQ.data ? (
          <ResumenCards resumen={resumenQ.data} />
        ) : null}

        {/* Tabla */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-wrap gap-3">
            <h2 className="font-semibold text-gray-900">
              Documentos de la flota
              {documentosQ.data && (
                <span className="ml-2 text-sm font-normal text-gray-400">
                  ({documentosQ.data.length})
                </span>
              )}
            </h2>
            <div className="flex gap-1">
              {FILTROS.map((f) => (
                <button
                  key={f.label}
                  onClick={() => setFiltro(f.value)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    filtro === f.value
                      ? "bg-slate-900 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <div className="p-2">
            {documentosQ.isLoading ? (
              <div className="py-12 text-center text-gray-400">Cargando...</div>
            ) : documentosQ.isError ? (
              <div className="py-12 text-center text-red-400">Error al cargar documentos</div>
            ) : (
              <FlotaTable
                documentos={documentosQ.data ?? []}
                conductores={conductoresQ.data ?? []}
              />
            )}
          </div>
        </div>

        {/* Feedback de acciones */}
        {syncMsg && (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg px-4 py-3 text-sm">
            {syncMsg}
          </div>
        )}
        {notifMsg && (
          <div className="bg-blue-50 border border-blue-200 text-blue-800 rounded-lg px-4 py-3 text-sm">
            {notifMsg}
          </div>
        )}
      </main>
    </div>
  );
}
