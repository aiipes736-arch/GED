import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import { FolderOpen, Plus, Pencil, Trash2 } from "lucide-react";

export default function Folders() {
  const [folders, setFolders] = useState([]);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ name: "", description: "" });

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/folders");
      setFolders(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const save = async (e) => {
    e?.preventDefault?.();
    try {
      if (edit) {
        await api.put(`/folders/${edit.id}`, { name: form.name, description: form.description });
        toast.success("Dossier mis à jour");
      } else {
        await api.post("/folders", { name: form.name, description: form.description });
        toast.success("Dossier créé");
      }
      setOpen(false);
      setEdit(null);
      setForm({ name: "", description: "" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const remove = async (f) => {
    if (!window.confirm(`Supprimer le dossier « ${f.name} » ? (les documents ne seront pas supprimés)`)) return;
    try {
      await api.delete(`/folders/${f.id}`);
      toast.success("Dossier supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <div className="space-y-6" data-testid="folders-page">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Organisation</div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>Dossiers</h1>
          <p className="text-sm text-gray-500 mt-1">{folders.length} dossier{folders.length > 1 ? "s" : ""}</p>
        </div>
        <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) { setEdit(null); setForm({ name: "", description: "" }); } }}>
          <DialogTrigger asChild>
            <Button className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="new-folder-btn" onClick={() => { setEdit(null); setForm({ name: "", description: "" }); }}>
              <Plus size={16} className="mr-2" /> Nouveau dossier
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>{edit ? "Modifier le dossier" : "Nouveau dossier"}</DialogTitle></DialogHeader>
            <form onSubmit={save} className="space-y-3">
              <div><Label>Nom *</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required data-testid="folder-name" /></div>
              <div><Label>Description</Label><Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="folder-desc" /></div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
                <Button type="submit" className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="folder-submit">Enregistrer</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {folders.length === 0 ? (
        <div className="inst-card p-12 text-center text-gray-500">
          <FolderOpen size={42} className="mx-auto text-gray-300 mb-3" />
          Aucun dossier. Créez votre premier dossier pour organiser vos documents.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {folders.map((f) => (
            <div key={f.id} className="inst-card p-5 group" data-testid={`folder-${f.id}`}>
              <div className="flex items-start justify-between">
                <div className="w-11 h-11 rounded-md bg-[#e8f3ed] text-[#0f4c3a] flex items-center justify-center">
                  <FolderOpen size={20} />
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button size="icon" variant="ghost" onClick={() => { setEdit(f); setForm({ name: f.name, description: f.description || "" }); setOpen(true); }}>
                    <Pencil size={14} />
                  </Button>
                  <Button size="icon" variant="ghost" onClick={() => remove(f)} className="text-red-600 hover:text-red-700 hover:bg-red-50">
                    <Trash2 size={14} />
                  </Button>
                </div>
              </div>
              <div className="font-semibold text-gray-900 mt-4 truncate" style={{ fontFamily: "Work Sans" }}>{f.name}</div>
              {f.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{f.description}</p>}
              <div className="text-[11px] uppercase tracking-wider text-gray-400 mt-4 pt-4 border-t border-gray-100">
                Créé {formatDate(f.created_at)} · {f.created_by_name}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
