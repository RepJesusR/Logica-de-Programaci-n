import { type EstadoDocumento } from "../services/api";

const CONFIG: Record<EstadoDocumento, { label: string; classes: string }> = {
  VIGENTE: { label: "Vigente", classes: "bg-green-100 text-green-800" },
  POR_VENCER: { label: "Por vencer", classes: "bg-yellow-100 text-yellow-800" },
  VENCIDO: { label: "Vencido", classes: "bg-red-100 text-red-800" },
  SIN_DOCUMENTO: { label: "Sin documento", classes: "bg-gray-100 text-gray-600" },
};

export function EstadoBadge({ estado }: { estado: EstadoDocumento }) {
  const { label, classes } = CONFIG[estado];
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${classes}`}>
      {label}
    </span>
  );
}
