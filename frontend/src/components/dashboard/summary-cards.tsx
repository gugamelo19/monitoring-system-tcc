import { DashboardSummary } from "@/types/dashboard";

type Props = {
  summary: DashboardSummary;
};

type CardItem = {
  label: string;
  value: number;
  description: string;
  valueClassName?: string;
};

export function SummaryCards({ summary }: Props) {
  const items: CardItem[] = [
    {
      label: "Ativos totais",
      value: summary.assets.total,
      description: "Quantidade total de ativos monitorados",
      valueClassName: "text-white",
    },
    {
      label: "Ativos online",
      value: summary.assets.online,
      description: "Ativos operando normalmente",
      valueClassName: "text-emerald-400",
    },
    {
      label: "Ativos offline",
      value: summary.assets.offline,
      description: "Ativos indisponíveis no momento",
      valueClassName: "text-red-400",
    },
    {
      label: "Ativos instáveis",
      value: summary.assets.unstable,
      description: "Ativos com comportamento intermitente",
      valueClassName: "text-amber-400",
    },
    {
      label: "Eventos",
      value: summary.events.total,
      description: "Eventos de rede registrados",
      valueClassName: "text-sky-400",
    },
    {
      label: "Anomalias",
      value: summary.anomalies.total,
      description: "Comportamentos anômalos detectados",
      valueClassName: "text-fuchsia-400",
    },
    {
      label: "Alertas abertos",
      value: summary.alerts.open,
      description: "Alertas aguardando tratamento",
      valueClassName: "text-red-400",
    },
    {
      label: "Alertas resolvidos",
      value: summary.alerts.resolved,
      description: "Alertas já finalizados",
      valueClassName: "text-emerald-400",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-2xl border border-slate-800 bg-slate-900 p-5 shadow-sm transition hover:border-slate-700"
        >
          <p className="text-sm text-slate-400">{item.label}</p>
          <h3 className={`mt-2 text-3xl font-bold ${item.valueClassName ?? "text-white"}`}>
            {item.value}
          </h3>
          <p className="mt-2 text-xs text-slate-500">{item.description}</p>
        </div>
      ))}
    </div>
  );
}