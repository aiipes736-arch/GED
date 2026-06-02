import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Navigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import { FileBarChart, Download, RefreshCw, Award, Users } from "lucide-react";

const MONTHS = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

export default function Reports() {
  const { user } = useAuth();
  const now = new Date();
  const [year, setYear] = useState(String(now.getFullYear()));
  const [month, setMonth] = useState(String(now.getMonth() + 1));
  const [agentId, setAgentId] = useState("all");
  const [agents, setAgents] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const yearOptions = [];
  for (let y = now.getFullYear(); y >= now.getFullYear() - 5; y--) yearOptions.push(String(y));

  const loadAgents = useCallback(async () => {
    try {
      const { data } = await api.get("/users");
      setAgents(data);
    } catch (err) {
      console.error("Reports.loadAgents failed:", err);
    }
  }, []);

  const loadPreview = useCallback(async () => {
    setLoading(true);
    try {
      const params = { year: Number(year), month: Number(month) };
      if (agentId && agentId !== "all") params.agent_id = agentId;
      const { data } = await api.get("/reports/monthly", { params });
      setData(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  }, [year, month, agentId]);

  useEffect(() => {
    if (user?.role === "admin") {
      loadAgents();
      loadPreview();
    }
  }, [user, loadAgents, loadPreview]);

  if (user && user.role !== "admin") return <Navigate to="/" replace />;

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      const params = { year: Number(year), month: Number(month) };
      if (agentId && agentId !== "all") params.agent_id = agentId;
      const res = await api.get("/reports/monthly/pdf", { params, responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rapport-mhcged-${year}-${String(month).padStart(2, "0")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success("Rapport téléchargé");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            Pilotage
          </div>
          <h1
            className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900"
            style={{ fontFamily: "Work Sans" }}
          >
            Rapports mensuels
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Synthèse d'activité officielle au format PDF — Top documents et agents les plus actifs
          </p>
        </div>
        <Button
          onClick={downloadPdf}
          disabled={downloading || loading}
          className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
          data-testid="download-pdf-btn"
        >
          <Download size={16} className="mr-2" />
          {downloading ? "Génération..." : "Télécharger le PDF"}
        </Button>
      </div>

      <div className="inst-card p-5">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <Label className="text-xs uppercase tracking-wider text-gray-500">Mois</Label>
            <Select value={month} onValueChange={setMonth}>
              <SelectTrigger data-testid="report-month">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MONTHS.map((m, i) => (
                  <SelectItem key={m} value={String(i + 1)}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs uppercase tracking-wider text-gray-500">Année</Label>
            <Select value={year} onValueChange={setYear}>
              <SelectTrigger data-testid="report-year">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {yearOptions.map((y) => (
                  <SelectItem key={y} value={y}>
                    {y}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="sm:col-span-1">
            <Label className="text-xs uppercase tracking-wider text-gray-500">Agent</Label>
            <Select value={agentId} onValueChange={setAgentId}>
              <SelectTrigger data-testid="report-agent">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les agents</SelectItem>
                {agents.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            variant="outline"
            onClick={loadPreview}
            disabled={loading}
            data-testid="report-refresh"
          >
            <RefreshCw size={14} className={`mr-2 ${loading ? "animate-spin" : ""}`} />
            {loading ? "Chargement..." : "Actualiser"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="inst-card p-6" data-testid="top-docs-card">
          <div className="flex items-center gap-2 mb-4">
            <Award size={18} className="text-[#0f4c3a]" />
            <h2 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "Work Sans" }}>
              Top documents téléchargés
            </h2>
          </div>
          {data && data.top_docs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50 hover:bg-gray-50">
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Document</TableHead>
                  <TableHead className="text-right">Téléch.</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.top_docs.map((d, i) => (
                  <TableRow key={d.id}>
                    <TableCell className="text-gray-500">{i + 1}</TableCell>
                    <TableCell className="font-medium text-gray-900">{d.title}</TableCell>
                    <TableCell className="text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#e8f3ed] text-[#0f4c3a] text-xs font-semibold">
                        {d.count}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-sm text-gray-500 py-8 text-center">
              {loading ? "Chargement..." : "Aucun téléchargement pour cette période."}
            </div>
          )}
        </div>

        <div className="inst-card p-6" data-testid="top-agents-card">
          <div className="flex items-center gap-2 mb-4">
            <Users size={18} className="text-[#0f4c3a]" />
            <h2 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "Work Sans" }}>
              Agents les plus actifs
            </h2>
          </div>
          {data && data.top_agents.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50 hover:bg-gray-50">
                  <TableHead className="w-12">#</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.top_agents.map((a, i) => (
                  <TableRow key={a.id}>
                    <TableCell className="text-gray-500">{i + 1}</TableCell>
                    <TableCell className="font-medium text-gray-900">{a.name}</TableCell>
                    <TableCell className="text-right">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#fef3c7] text-amber-800 text-xs font-semibold">
                        {a.count}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-sm text-gray-500 py-8 text-center">
              {loading ? "Chargement..." : "Aucune activité d'agent pour cette période."}
            </div>
          )}
        </div>
      </div>

      {data && (
        <div className="text-xs text-gray-500 flex items-center gap-2">
          <FileBarChart size={14} />
          Périmètre : {data.scope_label} · Période : {MONTHS[Number(month) - 1]} {year}
        </div>
      )}
    </div>
  );
}
