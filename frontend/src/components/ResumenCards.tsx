import { FileCheck, AlertTriangle, XCircle, FileQuestion } from "lucide-react";
import type { ResumenFlota } from "../services/api";

interface CardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  colorClass: string;
}

function Card({ label, value, icon, colorClass }: CardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${colorClass}`}>{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}

export function ResumenCards({ resumen }: { resumen: ResumenFlota }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Card
        label="Vigentes"
        value={resumen.vigente}
        icon={<FileCheck size={22} className="text-green-700" />}
        colorClass="bg-green-50"
      />
      <Card
        label="Por vencer"
        value={resumen.por_vencer}
        icon={<AlertTriangle size={22} className="text-yellow-700" />}
        colorClass="bg-yellow-50"
      />
      <Card
        label="Vencidos"
        value={resumen.vencido}
        icon={<XCircle size={22} className="text-red-700" />}
        colorClass="bg-red-50"
      />
      <Card
        label="Sin documento"
        value={resumen.sin_documento}
        icon={<FileQuestion size={22} className="text-gray-500" />}
        colorClass="bg-gray-50"
      />
    </div>
  );
}
