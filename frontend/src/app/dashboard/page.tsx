"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { getAccessToken, clearAuthTokens } from "@/lib/auth-storage";
import {
  DashboardSummary,
  ProtocolItem,
  SeverityItem,
  RecentEvent,
  RecentAlert,
} from "@/types/dashboard";
import { SummaryCards } from "@/components/dashboard/summary-cards";
import { AssetStatusOverview } from "@/components/dashboard/asset-status-overview";
import { ProtocolsChart } from "@/components/dashboard/protocols-chart";
import { SeverityChart } from "@/components/dashboard/severity-chart";
import { RecentEventsTable } from "@/components/dashboard/recent-events-table";
import { RecentAlertsTable } from "@/components/dashboard/recent-alerts-table";

export default function DashboardPage() {
  const router = useRouter();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [protocols, setProtocols] = useState<ProtocolItem[]>([]);
  const [severity, setSeverity] = useState<SeverityItem[]>([]);
  const [events, setEvents] = useState<RecentEvent[]>([]);
  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardData() {
      const token = getAccessToken();

      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const [
          summaryData,
          protocolsData,
          severityData,
          eventsData,
          alertsData,
        ] = await Promise.all([
          apiFetch<DashboardSummary>("/api/dashboard/summary/", { token }),
          apiFetch<ProtocolItem[]>("/api/dashboard/protocols/", { token }),
          apiFetch<SeverityItem[]>("/api/dashboard/severity/", { token }),
          apiFetch<RecentEvent[]>("/api/dashboard/recent-events/?limit=10", { token }),
          apiFetch<RecentAlert[]>("/api/dashboard/recent-alerts/?limit=10", { token }),
        ]);

        setSummary(summaryData);
        setProtocols(protocolsData);
        setSeverity(severityData);
        setEvents(eventsData);
        setAlerts(alertsData);
      } catch (error) {
        console.error("Erro ao carregar dashboard:", error);
        clearAuthTokens();
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, [router]);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 p-6 text-white">
        <p>Carregando dashboard...</p>
      </main>
    );
  }

  if (!summary) {
    return (
      <main className="min-h-screen bg-slate-950 p-6 text-white">
        <p>Não foi possível carregar os dados.</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">InfraGuard Dashboard</h1>
            <p className="text-sm text-slate-400">
              Monitoramento inteligente de infraestrutura de TI
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/dashboard/alerts"
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-white transition hover:bg-slate-900"
            >
              Ver alertas
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

        <SummaryCards summary={summary} />

        <AssetStatusOverview
          total={summary.assets.total}
          online={summary.assets.online}
          offline={summary.assets.offline}
          unstable={summary.assets.unstable}
          unknown={summary.assets.unknown}
        />

        {summary.assets.offline > 0 ? (
          <div className="rounded-2xl border border-red-900 bg-red-500/10 p-4 text-red-300">
            Atenção: existem {summary.assets.offline} ativo(s) offline no momento.
          </div>
        ) : null}

        <div className="grid gap-6 xl:grid-cols-2">
          <ProtocolsChart data={protocols} />
          <SeverityChart data={severity} />
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <RecentEventsTable events={events} />
          <RecentAlertsTable alerts={alerts} />
        </div>
      </div>
    </main>
  );
}