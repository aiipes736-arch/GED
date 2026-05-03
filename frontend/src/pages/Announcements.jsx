import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Megaphone, Plus, Trash2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger, DialogDescription,
} from "../components/ui/dialog";

export default function Announcements() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", content: "", expires_at: "" });
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/announcements");
      setItems(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e?.preventDefault?.();
    setSubmitting(true);
    try {
      const payload = {
        title: form.title,
        content: form.content,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      };
      await api.post("/announcements", payload);
      toast.success("Annonce publiée — tous les agents notifiés");
      setOpen(false);
      setForm({ title: "", content: "", expires_at: "" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (a) => {
    if (!window.confirm(`Supprimer l'annonce « ${a.title} » ?`)) return;
    try {
      await api.delete(`/announcements/${a.id}`);
      toast.success("Annonce supprimée");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <div className="space-y-6" data-testid="announcements-page">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            Communication interne
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            Annonces
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {items.length} annonce{items.length > 1 ? "s" : ""} active{items.length > 1 ? "s" : ""}
          </p>
        </div>
        {isAdmin && (
          <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) setForm({ title: "", content: "", expires_at: "" }); }}>
            <DialogTrigger asChild>
              <Button className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="new-announcement-btn">
                <Plus size={16} className="mr-2" /> Nouvelle annonce
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Publier une annonce</DialogTitle>
                <DialogDescription>
                  Cette annonce sera visible par tous les agents et générera une notification.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={submit} className="space-y-3" data-testid="announcement-form">
                <div>
                  <Label>Titre *</Label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    required
                    data-testid="announcement-title"
                  />
                </div>
                <div>
                  <Label>Contenu *</Label>
                  <Textarea
                    value={form.content}
                    onChange={(e) => setForm({ ...form, content: e.target.value })}
                    required
                    rows={5}
                    data-testid="announcement-content"
                  />
                </div>
                <div>
                  <Label>Date d'expiration (optionnel)</Label>
                  <Input
                    type="datetime-local"
                    value={form.expires_at}
                    onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                    data-testid="announcement-expires"
                  />
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
                    data-testid="announcement-submit"
                  >
                    {submitting ? "Publication..." : "Publier"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {items.length === 0 ? (
        <div className="inst-card p-12 text-center text-gray-500">
          <Megaphone size={42} className="mx-auto text-gray-300 mb-3" />
          Aucune annonce active.
          {isAdmin && " Cliquez sur « Nouvelle annonce » pour en publier une."}
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((a) => (
            <div key={a.id} className="inst-card p-5" data-testid={`announcement-${a.id}`}>
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-md bg-[#fef3c7] text-amber-700 flex items-center justify-center flex-shrink-0">
                  <Megaphone size={18} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg font-semibold text-gray-900" style={{ fontFamily: "Work Sans" }}>
                      {a.title}
                    </h3>
                    {a.expires_at && (
                      <span className="text-[10px] uppercase tracking-wider bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                        Jusqu'au {formatDate(a.expires_at)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap leading-relaxed">{a.content}</p>
                  <div className="text-xs text-gray-500 mt-3">
                    Publié par <span className="font-medium">{a.author_name}</span> · {formatDate(a.created_at)}
                  </div>
                </div>
                {isAdmin && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(a)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 flex-shrink-0"
                    data-testid={`announcement-delete-${a.id}`}
                  >
                    <Trash2 size={14} />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
