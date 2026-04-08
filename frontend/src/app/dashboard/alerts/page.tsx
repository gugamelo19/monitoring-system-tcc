"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, updateAlertStatus } from "@/lib/api";
import { clearAuthTokens, getAccessToken } from "@/lib/auth-storage";
import { RecentAlert } from "@/types/dashboard";

function getSeverityBadge(severity: string) {
  switch (severity) {
    case "CRITICAL":
      return "bg-red-600/20 text-red-300 border border-red-500/30";
    case "HIGH":
      return "bg-orange-600/20 text-orange-300 border border-orange-500/30";
    case "MEDIUM":
      return "bg-yellow-600/20 text-yellow-300 border border-yellow-500/30";
    case "LOW":
      return "bg-emerald-600/20 text-emerald-300 border border-emerald-500/30";
    default:
      return "bg-slate-700 text-slate-300 border border-slate-600";
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "OPEN":
      return "bg-red-500/10 text-red-400 border border-red-500/30";
    case "IN_PROGRESS":
      return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    case "RESOLVED":
      return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    case "FALSE_POSITIVE":
      return "bg-slate-600/20 text-slate-300 border border-slate-500/30";
    default:
      return "bg-slate-700 text-slate-300 border border-slate-600";
  }
}

export default function AlertsPage() {
  const router = useRouter();

  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingAlertId, setUpdatingAlertId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAlerts = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const data = await apiFetch<RecentAlert[]>("/api/alerts/", { token });
      setAlerts(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Erro ao carregar alertas:", error);
      clearAuthTokens();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    fetchAlerts();

    const interval = setInterval(() => {
      fetchAlerts();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchAlerts]);

  async function handleUpdateStatus(alertId: string, status: string) {
    const token = getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      setUpdatingAlertId(alertId);
      await updateAlertStatus(alertId, status, token);
      await fetchAlerts();
    } catch (error) {
      console.error("Erro ao atualizar status do alerta:", error);
      window.alert("Não foi possível atualizar o status do alerta.");
    } finally {
      setUpdatingAlertId(null);
    }
  }

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesStatus =
        statusFilter === "ALL" || alert.status === statusFilter;

      const matchesSeverity =
        severityFilter === "ALL" || alert.severity === severityFilter;

      return matchesStatus && matchesSeverity;
    });
  }, [alerts, statusFilter, severityFilter]);

  function clearFilters() {
    setStatusFilter("ALL");
    setSeverityFilter("ALL");
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Alertas</h1>
            <p className="text-sm text-slate-400">
              Monitoramento e acompanhamento dos alertas gerados pelo sistema
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
                Refine a visualização dos alertas por status e severidade
              </p>
            </div>

            <div className="text-sm text-slate-300">
              Exibindo{" "}
              <span className="font-semibold text-white">
                {filteredAlerts.length}
              </span>{" "}
              de <span className="font-semibold text-white">{alerts.length}</span>{" "}
              alertas
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div>
              <label className="mb-2 block text-sm text-slate-300">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
              >
                <option value="ALL">Todos</option>
                <option value="OPEN">OPEN</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="RESOLVED">RESOLVED</option>
                <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm text-slate-300">Severidade</label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
              >
                <option value="ALL">Todas</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
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
            Carregando alertas...
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
            Nenhum alerta encontrado para os filtros selecionados.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400">
                  <tr>
                    <th className="px-4 py-4">Título</th>
                    <th className="px-4 py-4">Ativo</th>
                    <th className="px-4 py-4">Tipo</th>
                    <th className="px-4 py-4">Severidade</th>
                    <th className="px-4 py-4">Status</th>
                    <th className="px-4 py-4">Criado em</th>
                    <th className="px-4 py-4">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAlerts.map((item) => {
                    const isUpdating = updatingAlertId === item.id;

                    return (
                      <tr key={item.id} className="border-t border-slate-800 align-top">
                        <td className="px-4 py-4">
                          <div>
                            <p className="font-medium text-white">{item.title}</p>
                            <p className="mt-1 text-xs text-slate-400">{item.message}</p>
                          </div>
                        </td>

                        <td className="px-4 py-4">{item.asset_name}</td>
                        <td className="px-4 py-4">{item.anomaly_type}</td>

                        <td className="px-4 py-4">
                          <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${getSeverityBadge(item.severity)}`}>
                            {item.severity}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${getStatusBadge(item.status)}`}>
                            {item.status}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          {new Date(item.created_at).toLocaleString("pt-BR")}
                        </td>

                        <td className="px-4 py-4">
                          <div className="flex min-w-60 flex-wrap gap-2">
                            <button
                              onClick={() => handleUpdateStatus(item.id, "IN_PROGRESS")}
                              disabled={isUpdating}
                              className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-300 transition hover:bg-amber-500/20 disabled:opacity-50"
                            >
                              Em análise
                            </button>

                            <button
                              onClick={() => handleUpdateStatus(item.id, "RESOLVED")}
                              disabled={isUpdating}
                              className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300 transition hover:bg-emerald-500/20 disabled:opacity-50"
                            >
                              Resolver
                            </button>

                            <button
                              onClick={() => handleUpdateStatus(item.id, "FALSE_POSITIVE")}
                              disabled={isUpdating}
                              className="rounded-lg border border-slate-500/30 bg-slate-500/10 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-500/20 disabled:opacity-50"
                            >
                              Falso positivo
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}