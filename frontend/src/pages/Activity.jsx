import React, { useEffect, useState } from "react";
import api, { formatDate } from "../lib/api";
import { History } from "lucide-react";

const ACTION_LABELS = {
  login: "Connexion",
  logout: "Déconnexion",
  user_created: "Agent créé",
  user_updated: "Agent modifié",
  user_deleted: "Agent supprimé",
  folder_created: "Dossier créé",
  folder_updated: "Dossier modifié",
  folder_deleted: "Dossier supprimé",
  document_uploaded: "Document téléversé",
  document_updated: "Document modifié",
  document_deleted: "Document supprimé",
  document_downloaded: "Téléchargement",
  document_archived: "Archivage",
  document_unarchived: "Désarchivage",
  document_shared: "Partage",
};

export default function Activity() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    api.get("/activity").then((r) => setLogs(r.data)).catch(() => {});
  }, []);

  return (
    <div className="space-y-6" data-testid="activity-page">
      <div>
        <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Audit</div>
        <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>Journal d'activité</h1>
        <p className="text-sm text-gray-500 mt-1">Historique des actions effectuées sur la plateforme</p>
      </div>

      <div className="inst-card">
        {logs.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <History size={36} className="mx-auto text-gray-300 mb-3" />
            Aucune activité enregistrée.
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {logs.map((l) => (
              <li key={l.id} className="px-5 py-4 flex items-start gap-4" data-testid={`log-${l.id}`}>
                <div className="w-8 h-8 rounded-full bg-[#e8f3ed] text-[#0f4c3a] flex items-center justify-center flex-shrink-0">
                  <History size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{l.user_name}</span>
                    <span className="text-[11px] uppercase tracking-wider text-[#0f4c3a] bg-[#e8f3ed] px-2 py-0.5 rounded">
                      {ACTION_LABELS[l.action] || l.action}
                    </span>
                  </div>
                  {l.details && <p className="text-sm text-gray-600 mt-1">{l.details}</p>}
                </div>
                <div className="text-xs text-gray-500 whitespace-nowrap">{formatDate(l.timestamp)}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
