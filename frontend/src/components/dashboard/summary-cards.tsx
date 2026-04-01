import { DashboardSummary } from "@/types/dashboard";

type Props = {
  summary: DashboardSummary;
};

export function SummaryCards({ summary }: Props) {
  const items = [
    { label: "Ativos totais", value: summary.assets.total },
    { label: "Ativos online", value: summary.assets.online },
    { label: "Eventos", value: summary.events.total },
    { label: "Anomalias", value: summary.anomalies.total },
    { label: "Alertas abertos", value: summary.alerts.open },
    { label: "Alertas resolvidos", value: summary.alerts.resolved },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-sm"
        >
          <p className="text-sm text-slate-400">{item.label}</p>
          <h3 className="mt-2 text-3xl font-bold text-white">{item.value}</h3>
        </div>
      ))}
    </div>
  );
}