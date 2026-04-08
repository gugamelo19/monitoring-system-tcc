"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { clearAuthTokens, getAccessToken } from "@/lib/auth-storage";
import { RecentEvent } from "@/types/dashboard";

function getProtocolBadge(protocol: string) {
  switch (protocol) {
    case "ICMP":
      return "bg-cyan-600/20 text-cyan-300 border border-cyan-500/30";
    case "TCP":
      return "bg-violet-600/20 text-violet-300 border border-violet-500/30";
    case "DNS":
      return "bg-emerald-600/20 text-emerald-300 border border-emerald-500/30";
    default:
      return "bg-slate-700 text-slate-300 border border-slate-600";
  }
}

export default function EventsPage() {
  const router = useRouter();

  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [protocolFilter, setProtocolFilter] = useState("ALL");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchEvents = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const data = await apiFetch<RecentEvent[]>("/api/events/", { token });
      setEvents(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Erro ao carregar eventos:", error);
      clearAuthTokens();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    fetchEvents();

    const interval = setInterval(() => {
      fetchEvents();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchEvents]);

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (protocolFilter === "ALL") return true;
      return event.protocol === protocolFilter;
    });
  }, [events, protocolFilter]);

  function clearFilters() {
    setProtocolFilter("ALL");
  }

  function formatEventDetails(event: RecentEvent) {
    if (event.protocol === "TCP") {
      return `Porta destino: ${event.destination_port ?? "-"} | Flags: ${event.tcp_flags ?? "-"}`;
    }

    if (event.protocol === "DNS") {
      return `Consulta: ${event.dns_query ?? "-"}`;
    }

    if (event.protocol === "ICMP") {
      return `Tipo: ${event.icmp_type ?? "-"} | Código: ${event.icmp_code ?? "-"}`;
    }

    return event.raw_summary ?? "-";
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Eventos de Rede</h1>
            <p className="text-sm text-slate-400">
              Visualização detalhada dos eventos coletados pelo sistema
            </p>
            {lastUpdated ? (
              <p className="mt-1 text-xs text-slate-500">
                Última atualização: {lastUpdated.toLocaleTimeString("pt-BR")}
              </p>
            ) : null}
          </div>

          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-white transition hover:bg-slate-900"
            >
              Voltar para dashboard
            </Link>

            <button
              onClick={() => {
                clearAuthTokens();
                router.push("/login");
              }}
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-white transition hover:bg-slate-900"
            >
              Sair
            </button>
          </div>
        </header>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-4 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Filtros</h2>
              <p className="text-sm text-slate-400">
                Refine a visualização por protocolo
              </p>
            </div>

            <div className="text-sm text-slate-300">
              Exibindo{" "}
              <span className="font-semibold text-white">
                {filteredEvents.length}
              </span>{" "}
              de <span className="font-semibold text-white">{events.length}</span>{" "}
              eventos
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div>
              <label className="mb-2 block text-sm text-slate-300">Protocolo</label>
              <select
                value={protocolFilter}
                onChange={(e) => setProtocolFilter(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
              >
                <option value="ALL">Todos</option>
                <option value="ICMP">ICMP</option>
                <option value="TCP">TCP</option>
                <option value="DNS">DNS</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="w-full rounded-xl border border-slate-700 px-4 py-3 text-sm text-white transition hover:bg-slate-950"
              >
                Limpar filtros
              </button>
            </div>
          </div>
        </section>

        {loading ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
            Carregando eventos...
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
            Nenhum evento encontrado para o filtro selecionado.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400">
                  <tr>
                    <th className="px-4 py-4">Ativo</th>
                    <th className="px-4 py-4">Protocolo</th>
                    <th className="px-4 py-4">Origem</th>
                    <th className="px-4 py-4">Destino</th>
                    <th className="px-4 py-4">Detalhes</th>
                    <th className="px-4 py-4">Coletor</th>
                    <th className="px-4 py-4">Data/Hora</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map((event) => (
                    <tr key={event.id} className="border-t border-slate-800 align-top">
                      <td className="px-4 py-4">
                        <div>
                          <p className="font-medium text-white">{event.asset_name}</p>
                          <p className="mt-1 text-xs text-slate-400">{event.raw_summary ?? "-"}</p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${getProtocolBadge(event.protocol)}`}>
                          {event.protocol}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <div>
                          <p>{event.source_ip}</p>
                          <p className="mt-1 text-xs text-slate-400">
                            Porta: {event.source_port ?? "-"}
                          </p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <div>
                          <p>{event.destination_ip}</p>
                          <p className="mt-1 text-xs text-slate-400">
                            Porta: {event.destination_port ?? "-"}
                          </p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <p className="max-w-md text-sm text-slate-300">
                          {formatEventDetails(event)}
                        </p>
                      </td>

                      <td className="px-4 py-4">{event.collector_name ?? "-"}</td>

                      <td className="px-4 py-4">
                        {new Date(event.event_timestamp).toLocaleString("pt-BR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}