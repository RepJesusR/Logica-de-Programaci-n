import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import type { Documento, Conductor } from "../services/api";
import { EstadoBadge } from "./EstadoBadge";

interface Props {
  documentos: Documento[];
  conductores: Conductor[];
}

function conductorNombre(conductores: Conductor[], id: string): string {
  const c = conductores.find((c) => c.id === id);
  if (!c) return id;
  return [c.nombre, c.apellido].filter(Boolean).join(" ") || c.nro_documento;
}

export function FlotaTable({ documentos, conductores }: Props) {
  if (documentos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        No hay documentos para mostrar.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-100">
        <thead className="bg-gray-50">
          <tr>
            {["Conductor", "Documento", "Vence", "Días restantes", "Estado"].map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-50">
          {documentos.map((doc) => (
            <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                {conductorNombre(conductores, doc.conductor_id)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-700">
                {doc.tipo_documento_nombre}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {doc.fecha_vencimiento
                  ? format(parseISO(doc.fecha_vencimiento), "dd/MM/yyyy", { locale: es })
                  : "—"}
              </td>
              <td className="px-4 py-3 text-sm">
                {doc.dias_para_vencer !== null ? (
                  <span
                    className={
                      doc.dias_para_vencer < 0
                        ? "text-red-700 font-semibold"
                        : doc.dias_para_vencer <= doc.dias_preaviso
                        ? "text-yellow-700 font-semibold"
                        : "text-gray-600"
                    }
                  >
                    {doc.dias_para_vencer < 0
                      ? `Venció hace ${Math.abs(doc.dias_para_vencer)}d`
                      : `${doc.dias_para_vencer}d`}
                  </span>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-4 py-3">
                <EstadoBadge estado={doc.estado} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
