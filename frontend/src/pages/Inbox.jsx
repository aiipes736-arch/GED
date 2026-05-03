import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatBytes, formatDate } from "../lib/api";
import { Inbox as InboxIcon, FileText, Download, Eye } from "lucide-react";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";

export default function Inbox() {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/inbox");
      setItems(data.items);
      setUnread(data.unread_count);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const markRead = async (d) => {
    try {
      await api.post(`/inbox/${d.id}/read`);
      load();
    } catch {
      // silent
    }
  };

  const downloadDoc = async (d) => {
    try {
      const res = await api.get(`/documents/${d.id}/download`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = d.original_filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      if (!d.is_read) markRead(d);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <div className="space-y-6" data-testid="inbox-page">
      <div>
        <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
          Documents reçus
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
          Boîte de réception
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {items.length} document{items.length > 1 ? "s" : ""} partagé{items.length > 1 ? "s" : ""} avec vous · {unread} non lu{unread > 1 ? "s" : ""}
        </p>
      </div>

      {loading ? (
        <div className="inst-card p-12 text-center text-gray-500">Chargement...</div>
      ) : items.length === 0 ? (
        <div className="inst-card p-12 text-center text-gray-500">
          <InboxIcon size={42} className="mx-auto text-gray-300 mb-3" />
          Votre boîte est vide. Lorsqu'un agent partagera un document avec vous, il apparaîtra ici.
        </div>
      ) : (
        <ul className="inst-card divide-y divide-gray-100">
          {items.map((d) => (
            <li
              key={d.id}
              className={`px-5 py-4 flex items-center gap-4 ${!d.is_read ? "bg-[#f0fdf4]" : ""}`}
              data-testid={`inbox-item-${d.id}`}
            >
              <div className="w-10 h-10 rounded-md bg-[#e8f3ed] text-[#0f4c3a] flex items-center justify-center flex-shrink-0">
                <FileText size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <div className="font-semibold text-gray-900 truncate">{d.title}</div>
                  {!d.is_read && (
                    <Badge className="bg-[#dc241f] hover:bg-[#dc241f] text-white text-[10px]">
                      Nouveau
                    </Badge>
                  )}
                  {d.is_archived && (
                    <Badge variant="secondary" className="text-[10px]">Archivé</Badge>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-0.5 truncate">
                  Partagé par <span className="font-medium">{d.uploaded_by_name}</span> · {d.original_filename} · {formatBytes(d.size)} · {formatDate(d.created_at)}
                </div>
                {d.tags?.length > 0 && (
                  <div className="flex gap-1 mt-1.5 flex-wrap">
                    {d.tags.slice(0, 4).map((t) => (
                      <span key={t} className="inline-block bg-gray-100 text-gray-700 text-[10px] px-1.5 py-0.5 rounded">{t}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2 flex-shrink-0">
                {!d.is_read && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => markRead(d)}
                    className="text-[#0f4c3a]"
                    data-testid={`inbox-read-${d.id}`}
                  >
                    <Eye size={14} className="mr-1" /> Marquer lu
                  </Button>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadDoc(d)}
                  data-testid={`inbox-download-${d.id}`}
                >
                  <Download size={14} className="mr-1" /> Télécharger
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
