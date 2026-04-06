"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { apiFetch, updateAsset } from "@/lib/api";
import { clearAuthTokens, getAccessToken } from "@/lib/auth-storage";
import { Asset } from "@/types/assets";

type FormState = {
  name: string;
  hostname: string;
  ip_address: string;
  mac_address: string;
  asset_type: string;
  location: string;
  operating_system: string;
  status: string;
  is_monitored: boolean;
};

const initialFormState: FormState = {
  name: "",
  hostname: "",
  ip_address: "",
  mac_address: "",
  asset_type: "OTHER",
  location: "",
  operating_system: "",
  status: "UNKNOWN",
  is_monitored: true,
};

export default function EditAssetPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const assetId = String(params.id);

  const [form, setForm] = useState<FormState>(initialFormState);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function updateField<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  const fetchAsset = useCallback(async () => {
    const token = getAccessToken();

    if (!token) {
      clearAuthTokens();
      router.push("/login");
      return;
    }

    try {
      const data = await apiFetch<Asset>(`/api/assets/${assetId}/`, { token });

      setForm({
        name: data.name,
        hostname: data.hostname ?? "",
        ip_address: data.ip_address,
        mac_address: data.mac_address ?? "",
        asset_type: data.asset_type,
        location: data.location ?? "",
        operating_system: data.operating_system ?? "",
        status: data.status,
        is_monitored: data.is_monitored,
      });
    } catch (error) {
      console.error("Erro ao carregar ativo:", error);
      setError("Não foi possível carregar o ativo.");
    } finally {
      setLoading(false);
    }
  }, [assetId, router]);

  useEffect(() => {
    fetchAsset();
  }, [fetchAsset]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const token = getAccessToken();

    if (!token) {
      clearAuthTokens();
      router.push("/login");
      return;
    }

    try {
      await updateAsset(
        assetId,
        {
          name: form.name,
          hostname: form.hostname || null,
          ip_address: form.ip_address,
          mac_address: form.mac_address || null,
          asset_type: form.asset_type,
          location: form.location || null,
          operating_system: form.operating_system || null,
          status: form.status,
          is_monitored: form.is_monitored,
        },
        token
      );

      router.push("/dashboard/assets");
    } catch (error) {
      console.error("Erro ao atualizar ativo:", error);

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Não foi possível atualizar o ativo.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Editar Ativo</h1>
            <p className="text-sm text-slate-400">
              Atualize as informações do ativo monitorado
            </p>
          </div>

          <div className="flex gap-3">
            <Link
              href="/dashboard/assets"
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-white transition hover:bg-slate-900"
            >
              Voltar para ativos
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

        {loading ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-slate-300">
            Carregando ativo...
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
          >
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm text-slate-300">Nome *</label>
                <input
                  value={form.name}
                  onChange={(e) => updateField("name", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">Hostname</label>
                <input
                  value={form.hostname}
                  onChange={(e) => updateField("hostname", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">IP *</label>
                <input
                  value={form.ip_address}
                  onChange={(e) => updateField("ip_address", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">MAC Address</label>
                <input
                  value={form.mac_address}
                  onChange={(e) => updateField("mac_address", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">Tipo</label>
                <select
                  value={form.asset_type}
                  onChange={(e) => updateField("asset_type", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                >
                  <option value="SERVER">SERVER</option>
                  <option value="ROUTER">ROUTER</option>
                  <option value="SWITCH">SWITCH</option>
                  <option value="FIREWALL">FIREWALL</option>
                  <option value="WORKSTATION">WORKSTATION</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => updateField("status", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                >
                  <option value="ONLINE">ONLINE</option>
                  <option value="OFFLINE">OFFLINE</option>
                  <option value="UNSTABLE">UNSTABLE</option>
                  <option value="UNKNOWN">UNKNOWN</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">Localização</label>
                <input
                  value={form.location}
                  onChange={(e) => updateField("location", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">Sistema Operacional</label>
                <input
                  value={form.operating_system}
                  onChange={(e) => updateField("operating_system", e.target.value)}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none"
                />
              </div>
            </div>

            <div className="mt-4 flex items-center gap-3">
              <input
                id="is_monitored"
                type="checkbox"
                checked={form.is_monitored}
                onChange={(e) => updateField("is_monitored", e.target.checked)}
                className="h-4 w-4"
              />
              <label htmlFor="is_monitored" className="text-sm text-slate-300">
                Ativo monitorado
              </label>
            </div>

            {error ? <p className="mt-4 text-sm text-red-400">{error}</p> : null}

            <div className="mt-6 flex gap-3">
              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-slate-100 px-5 py-3 font-medium text-slate-900 transition hover:opacity-90 disabled:opacity-60"
              >
                {saving ? "Salvando..." : "Salvar alterações"}
              </button>

              <Link
                href="/dashboard/assets"
                className="rounded-xl border border-slate-700 px-5 py-3 text-sm text-white transition hover:bg-slate-950"
              >
                Cancelar
              </Link>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}