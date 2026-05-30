import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatBytes, formatDate } from "../lib/api";
import { FileText, FolderOpen, Users, Archive, HardDrive, TrendingUp, Megaphone, Inbox, MessageSquare, Settings, LogOut, FileBarChart } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

function StatCard({ icon: Icon, label, value, accent, testId }) {
  return (
    <div className="inst-card p-5" data-testid={testId}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500 font-semibold">{label}</div>
          <div className="text-3xl font-bold text-gray-900 mt-2" style={{ fontFamily: "Work Sans" }}>{value}</div>
        </div>
        <div className={`w-10 h-10 rounded-md flex items-center justify-center ${accent}`}>
          <Icon size={18} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [announcements, setAnnouncements] = useState([]);

  useEffect(() => {
    api.get("/dashboard/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/announcements").then((r) => setAnnouncements(r.data.slice(0, 3))).catch(() => {});
  }, []);

  const isAdmin = user?.role === "admin";

  const tiles = [
    { to: "/documents", label: "Documents", icon: FileText, color: "bg-[#e8f3ed] text-[#0f4c3a]", testId: "tile-documents" },
    { to: "/folders", label: "Dossiers", icon: FolderOpen, color: "bg-amber-50 text-amber-700", testId: "tile-folders" },
    { to: "/inbox", label: "Boîte réception", icon: Inbox, color: "bg-blue-50 text-blue-700", testId: "tile-inbox" },
    { to: "/messages", label: "Messagerie", icon: MessageSquare, color: "bg-purple-50 text-purple-700", testId: "tile-messages" },
    { to: "/announcements", label: "Annonces", icon: Megaphone, color: "bg-yellow-50 text-yellow-700", testId: "tile-announcements" },
    ...(isAdmin ? [
      { to: "/agents", label: "Agents", icon: Users, color: "bg-cyan-50 text-cyan-700", testId: "tile-agents" },
      { to: "/reports", label: "Rapports", icon: FileBarChart, color: "bg-indigo-50 text-indigo-700", testId: "tile-reports" },
      { to: "/settings", label: "Paramètres", icon: Settings, color: "bg-gray-100 text-gray-700", testId: "tile-settings" },
    ] : []),
  ];

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Vue d'ensemble</div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            Bonjour, {user?.name?.split(" ")[0] || "Agent"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Aperçu de votre plateforme MHCGED — {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
          </p>
        </div>
        <button
          onClick={async () => { await logout(); navigate("/login"); }}
          className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-red-600 px-3 py-2 rounded-md hover:bg-red-50 transition-colors"
          data-testid="dashboard-logout"
        >
          <LogOut size={14} /> Se déconnecter
        </button>
      </div>

      {announcements.length > 0 && (
        <div className="space-y-3" data-testid="dashboard-announcements">
          {announcements.map((a) => (
            <div
              key={a.id}
              className="rounded-lg border border-amber-200 bg-amber-50/60 px-4 py-3 flex items-start gap-3"
            >
              <div className="w-8 h-8 rounded-md bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0">
                <Megaphone size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-gray-900">{a.title}</div>
                <p className="text-sm text-gray-700 mt-0.5 whitespace-pre-wrap">{a.content}</p>
                <div className="text-[11px] text-gray-500 mt-1">
                  Publié par {a.author_name} · {formatDate(a.created_at)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <div className="text-[11px] uppercase tracking-[0.2em] text-gray-500 font-semibold mb-3">Accès rapides</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3" data-testid="quick-tiles">
          {tiles.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.to}
                onClick={() => navigate(t.to)}
                className="inst-card p-4 hover:shadow-md transition-shadow text-left group"
                data-testid={t.testId}
              >
                <div className={`w-10 h-10 rounded-md flex items-center justify-center mb-3 ${t.color} group-hover:scale-105 transition-transform`}>
                  <Icon size={18} />
                </div>
                <div className="text-sm font-medium text-gray-900">{t.label}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          icon={FileText}
          label="Documents actifs"
          value={stats?.total_documents ?? "—"}
          accent="bg-[#e8f3ed] text-[#0f4c3a]"
          testId="stat-documents"
        />
        <StatCard
          icon={FolderOpen}
          label="Dossiers"
          value={stats?.total_folders ?? "—"}
          accent="bg-amber-50 text-amber-700"
          testId="stat-folders"
        />
        <StatCard
          icon={Archive}
          label="Archives"
          value={stats?.total_archived ?? "—"}
          accent="bg-red-50 text-[#dc241f]"
          testId="stat-archived"
        />
        {user?.role === "admin" ? (
          <StatCard
            icon={Users}
            label="Agents"
            value={stats?.total_agents ?? "—"}
            accent="bg-blue-50 text-blue-700"
            testId="stat-agents"
          />
        ) : (
          <StatCard
            icon={HardDrive}
            label="Espace utilisé"
            value={stats ? formatBytes(stats.total_size) : "—"}
            accent="bg-gray-100 text-gray-700"
            testId="stat-storage"
          />
        )}
      </div>

      <div className="inst-card p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500 font-semibold">Activité</div>
            <h2 className="text-xl font-semibold text-gray-900 mt-1" style={{ fontFamily: "Work Sans" }}>
              Documents récents
            </h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <TrendingUp size={14} />
            {stats ? formatBytes(stats.total_size) : "—"} stockés
          </div>
        </div>
        {stats?.recent_documents?.length ? (
          <ul className="divide-y divide-gray-100">
            {stats.recent_documents.map((d) => (
              <li key={d.id} className="py-3 flex items-center gap-4" data-testid={`recent-doc-${d.id}`}>
                <div className="w-9 h-9 rounded-md bg-gray-100 flex items-center justify-center text-gray-500">
                  <FileText size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">{d.title}</div>
                  <div className="text-xs text-gray-500 mt-0.5 truncate">
                    {d.original_filename} · par {d.uploaded_by_name || "Agent"}
                  </div>
                </div>
                <div className="text-xs text-gray-500 whitespace-nowrap">{formatDate(d.created_at)}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-gray-500 py-8 text-center">Aucun document récent. Importez votre premier document.</div>
        )}
      </div>
    </div>
  );
}
