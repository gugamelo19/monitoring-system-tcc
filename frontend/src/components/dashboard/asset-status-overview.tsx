type Props = {
  total: number;
  online: number;
  offline: number;
  unstable: number;
  unknown?: number;
};

type StatusItem = {
  label: string;
  value: number;
  dotClassName: string;
  textClassName: string;
  bgClassName: string;
};

export function AssetStatusOverview({
  total,
  online,
  offline,
  unstable,
  unknown = 0,
}: Props) {
  const items: StatusItem[] = [
    {
      label: "Online",
      value: online,
      dotClassName: "bg-emerald-400",
      textClassName: "text-emerald-400",
      bgClassName: "bg-emerald-500/10",
    },
    {
      label: "Offline",
      value: offline,
      dotClassName: "bg-red-400",
      textClassName: "text-red-400",
      bgClassName: "bg-red-500/10",
    },
    {
      label: "Instável",
      value: unstable,
      dotClassName: "bg-amber-400",
      textClassName: "text-amber-400",
      bgClassName: "bg-amber-500/10",
    },
    {
      label: "Desconhecido",
      value: unknown,
      dotClassName: "bg-slate-400",
      textClassName: "text-slate-300",
      bgClassName: "bg-slate-500/10",
    },
  ];

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Status dos ativos</h2>
          <p className="text-sm text-slate-400">
            Visão operacional da infraestrutura monitorada
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-300">
          Total: <span className="font-semibold text-white">{total}</span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div
            key={item.label}
            className={`rounded-2xl border border-slate-800 p-4 ${item.bgClassName}`}
          >
            <div className="flex items-center gap-2">
              <span className={`h-2.5 w-2.5 rounded-full ${item.dotClassName}`} />
              <span className="text-sm text-slate-300">{item.label}</span>
            </div>

            <p className={`mt-3 text-3xl font-bold ${item.textClassName}`}>{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}