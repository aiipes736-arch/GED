import React, { useEffect, useState, useCallback, useMemo } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { FolderOpen, Plus, Pencil, Trash2, ChevronRight, ChevronDown, Folder } from "lucide-react";

function buildTree(folders) {
  const byId = new Map(folders.map((f) => [f.id, { ...f, children: [] }]));
  const roots = [];
  byId.forEach((f) => {
    if (f.parent_id && byId.has(f.parent_id)) {
      byId.get(f.parent_id).children.push(f);
    } else {
      roots.push(f);
    }
  });
  return roots;
}

function FolderRow({ node, depth, onEdit, onDelete, onAddChild, expanded, toggle }) {
  const isOpen = expanded.has(node.id);
  const hasChildren = node.children.length > 0;
  return (
    <>
      <div
        className="flex items-center gap-2 py-2.5 px-3 rounded-md hover:bg-gray-50 group border-b border-gray-100 last:border-0"
        style={{ paddingLeft: 12 + depth * 22 }}
        data-testid={`folder-${node.id}`}
      >
        <button
          onClick={() => hasChildren && toggle(node.id)}
          className={`w-5 h-5 flex items-center justify-center text-gray-400 ${
            hasChildren ? "hover:text-gray-700" : "invisible"
          }`}
          aria-label="toggle"
        >
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <div className="w-7 h-7 rounded bg-[#e8f3ed] text-[#0f4c3a] flex items-center justify-center flex-shrink-0">
          {hasChildren ? <FolderOpen size={14} /> : <Folder size={14} />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 truncate">{node.name}</div>
          {node.description && (
            <div className="text-xs text-gray-500 truncate">{node.description}</div>
          )}
        </div>
        <div className="text-xs text-gray-400 hidden md:block whitespace-nowrap mr-2">
          {node.created_by_name} · {formatDate(node.created_at)}
        </div>
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onAddChild(node)}
            title="Ajouter un sous-dossier"
            data-testid={`folder-add-child-${node.id}`}
          >
            <Plus size={14} />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onEdit(node)}
            data-testid={`folder-edit-${node.id}`}
          >
            <Pencil size={14} />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onDelete(node)}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            data-testid={`folder-delete-${node.id}`}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      </div>
      {isOpen &&
        node.children.map((c) => (
          <FolderRow
            key={c.id}
            node={c}
            depth={depth + 1}
            onEdit={onEdit}
            onDelete={onDelete}
            onAddChild={onAddChild}
            expanded={expanded}
            toggle={toggle}
          />
        ))}
    </>
  );
}

export default function Folders() {
  const [folders, setFolders] = useState([]);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ name: "", description: "", parent_id: "none" });
  const [expanded, setExpanded] = useState(new Set());

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/folders");
      setFolders(data);
      // expand all roots by default
      setExpanded((prev) => {
        const next = new Set(prev);
        data.forEach((f) => {
          if (!f.parent_id) next.add(f.id);
        });
        return next;
      });
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const tree = useMemo(() => buildTree(folders), [folders]);

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const openCreate = (parent = null) => {
    setEdit(null);
    setForm({ name: "", description: "", parent_id: parent ? parent.id : "none" });
    setOpen(true);
  };

  const openEdit = (f) => {
    setEdit(f);
    setForm({
      name: f.name,
      description: f.description || "",
      parent_id: f.parent_id || "none",
    });
    setOpen(true);
  };

  const save = async (e) => {
    e?.preventDefault?.();
    try {
      const payload = {
        name: form.name,
        description: form.description,
        parent_id: form.parent_id === "none" ? null : form.parent_id,
      };
      if (edit) {
        if (payload.parent_id === edit.id) {
          toast.error("Un dossier ne peut pas être son propre parent");
          return;
        }
        await api.put(`/folders/${edit.id}`, payload);
        toast.success("Dossier mis à jour");
      } else {
        await api.post("/folders", payload);
        toast.success("Dossier créé");
      }
      setOpen(false);
      setEdit(null);
      setForm({ name: "", description: "", parent_id: "none" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const remove = async (f) => {
    const childCount = folders.filter((x) => x.parent_id === f.id).length;
    const msg = childCount
      ? `« ${f.name} » contient ${childCount} sous-dossier(s) qui deviendront des dossiers racines. Continuer ?`
      : `Supprimer le dossier « ${f.name} » ? (les documents ne seront pas supprimés)`;
    if (!window.confirm(msg)) return;
    try {
      // detach children
      if (childCount) {
        await Promise.all(
          folders
            .filter((x) => x.parent_id === f.id)
            .map((c) => api.put(`/folders/${c.id}`, { parent_id: null }))
        );
      }
      await api.delete(`/folders/${f.id}`);
      toast.success("Dossier supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  // Parent options excluding the folder being edited and its descendants
  const descendantsOf = (id) => {
    const out = new Set([id]);
    let added = true;
    while (added) {
      added = false;
      for (const f of folders) {
        if (f.parent_id && out.has(f.parent_id) && !out.has(f.id)) {
          out.add(f.id);
          added = true;
        }
      }
    }
    return out;
  };
  const blockedIds = edit ? descendantsOf(edit.id) : new Set();

  return (
    <div className="space-y-6" data-testid="folders-page">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Organisation</div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>Dossiers</h1>
          <p className="text-sm text-gray-500 mt-1">
            {folders.length} dossier{folders.length > 1 ? "s" : ""} · arborescence hiérarchique
          </p>
        </div>
        <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) { setEdit(null); setForm({ name: "", description: "", parent_id: "none" }); } }}>
          <DialogTrigger asChild>
            <Button
              className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
              data-testid="new-folder-btn"
              onClick={() => openCreate()}
            >
              <Plus size={16} className="mr-2" /> Nouveau dossier
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{edit ? "Modifier le dossier" : "Nouveau dossier"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={save} className="space-y-3">
              <div>
                <Label>Nom *</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  data-testid="folder-name"
                />
              </div>
              <div>
                <Label>Dossier parent</Label>
                <Select
                  value={form.parent_id}
                  onValueChange={(v) => setForm({ ...form, parent_id: v })}
                >
                  <SelectTrigger data-testid="folder-parent">
                    <SelectValue placeholder="Aucun (racine)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Aucun (racine)</SelectItem>
                    {folders
                      .filter((f) => !blockedIds.has(f.id))
                      .map((f) => (
                        <SelectItem key={f.id} value={f.id}>
                          {f.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  data-testid="folder-desc"
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
                <Button
                  type="submit"
                  className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
                  data-testid="folder-submit"
                >
                  Enregistrer
                </Button>
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
        <div className="inst-card p-2">
          {tree.map((root) => (
            <FolderRow
              key={root.id}
              node={root}
              depth={0}
              onEdit={openEdit}
              onDelete={remove}
              onAddChild={openCreate}
              expanded={expanded}
              toggle={toggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
