import { RecentEvent } from "@/types/dashboard";

type Props = {
  events: RecentEvent[];
};

export function RecentEventsTable({ events }: Props) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Eventos recentes</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-3">Ativo</th>
              <th className="pb-3">Protocolo</th>
              <th className="pb-3">Origem</th>
              <th className="pb-3">Destino</th>
              <th className="pb-3">Data/Hora</th>
            </tr>
          </thead>
          <tbody>
            {events.map((event) => (
              <tr key={event.id} className="border-t border-slate-800">
                <td className="py-3">{event.asset_name}</td>
                <td className="py-3">{event.protocol}</td>
                <td className="py-3">{event.source_ip}</td>
                <td className="py-3">{event.destination_ip}</td>
                <td className="py-3">
                  {new Date(event.event_timestamp).toLocaleString("pt-BR")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}