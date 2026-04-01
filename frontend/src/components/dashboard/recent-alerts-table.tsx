import { RecentAlert } from "@/types/dashboard";

type Props = {
  alerts: RecentAlert[];
};

export function RecentAlertsTable({ alerts }: Props) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Alertas recentes</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-3">Título</th>
              <th className="pb-3">Ativo</th>
              <th className="pb-3">Tipo</th>
              <th className="pb-3">Severidade</th>
              <th className="pb-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert) => (
              <tr key={alert.id} className="border-t border-slate-800">
                <td className="py-3">{alert.title}</td>
                <td className="py-3">{alert.asset_name}</td>
                <td className="py-3">{alert.anomaly_type}</td>
                <td className="py-3">{alert.severity}</td>
                <td className="py-3">{alert.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}