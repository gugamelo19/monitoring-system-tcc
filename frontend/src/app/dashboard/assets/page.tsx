
"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { clearAuthTokens, getAccessToken } from "@/lib/auth-storage";
import { Asset } from "@/types/assets";

function getStatusBadge(status: string) {
  switch (status) {
    case "ONLINE":
      return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    case "OFFLINE":
      return "bg-red-500/10 text-red-400 border border-red-500/30";
    case "UNSTABLE":
      return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    case "UNKNOWN":
      return "bg-slate-600/20 text-slate-300 border border-slate-500/30";
    default:
      return "bg-slate-700 text-slate-300 border border-slate-600";
  }
}

function getMonitoredBadge(isMonitored: boolean) {
  return isMonitored
    ? "bg-sky-500/10 text-sky-300 border border-sky-500/30"
    : "bg-slate-600/20 text-slate-300 border border-slate-500/30";
}

export default function AssetsPage() {
  const router = useRouter();

  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const fetchAssets = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const data = await apiFetch<Asset[]>("/api/assets/", { token });
      setAssets(data);
    } catch (error) {
      console.error("Erro ao carregar ativos:", error);
      clearAuthTokens();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const assetTypes = useMemo(() => {
    const uniqueTypes = Array.from(new Set(assets.map((asset) => asset.asset_type)));
    return uniqueTypes.sort();
  }, [assets]);

  const filteredAssets = useMemo(() => {
    return assets.filter((asset) => {
      const matchesStatus = statusFilter === "ALL" || asset.status === statusFilter;
      const matchesType = typeFilter === "ALL" || asset.asset_type === typeFilter;

      return matchesStatus && matchesType;
    });
  }, [assets, statusFilter, typeFilter]);

  function clearFilters() {
    setStatusFilter("ALL");
    setTypeFilter("ALL");
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Ativos Monitorados</h1>
            <p className="text-sm text-slate-400">
              Inventário dos ativos acompanhados pelo sistema
            </p>
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
                Filtre ativos por status e tipo
              </p>
            </div>

            <div className="text-sm text-slate-300">
              Exibindo{" "}
              <span className="font-semibold text-white">{filteredAssets.length}</span>{" "}
              de <span className="font-semibold text-white">{assets.length}</span> ativos
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
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
                <option value="UNSTABLE">UNSTABLE</option>
                <option value="UNKNOWN">UNKNOWN</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm text-slate-300">Tipo</label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
              >
                <option value="ALL">Todos</option>
                {assetTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
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
            Carregando ativos...
          </div>
        ) : filteredAssets.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
            Nenhum ativo encontrado para os filtros selecionados.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-950 text-slate-400">
                  <tr>
                    <th className="px-4 py-4">Nome</th>
                    <th className="px-4 py-4">IP</th>
                    <th className="px-4 py-4">Hostname</th>
                    <th className="px-4 py-4">Tipo</th>
                    <th className="px-4 py-4">Localização</th>
                    <th className="px-4 py-4">Sistema</th>
                    <th className="px-4 py-4">Status</th>
                    <th className="px-4 py-4">Monitorado</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAssets.map((asset) => (
                    <tr key={asset.id} className="border-t border-slate-800">
                      <td className="px-4 py-4 font-medium text-white">{asset.name}</td>
                      <td className="px-4 py-4">{asset.ip_address}</td>
                      <td className="px-4 py-4">{asset.hostname ?? "-"}</td>
                      <td className="px-4 py-4">{asset.asset_type}</td>
                      <td className="px-4 py-4">{asset.location ?? "-"}</td>
                      <td className="px-4 py-4">{asset.operating_system ?? "-"}</td>
                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${getStatusBadge(asset.status)}`}
                        >
                          {asset.status}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${getMonitoredBadge(asset.is_monitored)}`}
                        >
                          {asset.is_monitored ? "SIM" : "NÃO"}
                        </span>
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