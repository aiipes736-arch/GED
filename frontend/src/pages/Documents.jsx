import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatBytes, formatDate } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator,
} from "../components/ui/dropdown-menu";
import {
  Upload, Search, FileText, MoreVertical, Download, Trash2, Archive, Pencil, Share2, MessageSquare, Send,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

export default function Documents({ archivedView = false }) {
  const { user } = useAuth();
  const [docs, setDocs] = useState([]);
  const [folders, setFolders] = useState([]);
  const [agents, setAgents] = useState([]);
  const [search, setSearch] = useState("");
  const [filterFolder, setFilterFolder] = useState("all");
  const [filterTag, setFilterTag] = useState("all");
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(false);

  const [uploadOpen, setUploadOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({ title: "", description: "", folder_id: "none", tags: "" });
  const [uploading, setUploading] = useState(false);

  const [editDoc, setEditDoc] = useState(null);
  const [shareDoc, setShareDoc] = useState(null);
  const [shareSelected, setShareSelected] = useState([]);
  const [commentsDoc, setCommentsDoc] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentDraft, setCommentDraft] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { archived: archivedView };
      if (search) params.search = search;
      if (filterFolder !== "all") params.folder_id = filterFolder;
      if (filterTag !== "all") params.tag = filterTag;
      const { data } = await api.get("/documents", { params });
      setDocs(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  }, [archivedView, search, filterFolder, filterTag]);

  useEffect(() => {
    load();
    api.get("/folders").then((r) => setFolders(r.data)).catch(() => {});
    api.get("/tags").then((r) => setTags(r.data)).catch(() => {});
    if (user?.role === "admin") {
      api.get("/users").then((r) => setAgents(r.data.filter((a) => a.id !== user.id))).catch(() => {});
    }
  }, [load, user]);

  const onUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error("Veuillez sélectionner un fichier");
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", form.title || file.name);
      fd.append("description", form.description);
      if (form.folder_id && form.folder_id !== "none") fd.append("folder_id", form.folder_id);
      fd.append("tags", form.tags);
      await api.post("/documents", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("Document téléversé avec succès");
      setUploadOpen(false);
      setFile(null);
      setForm({ title: "", description: "", folder_id: "none", tags: "" });
      load();
      api.get("/tags").then((r) => setTags(r.data)).catch(() => {});
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setUploading(false);
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
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const deleteDoc = async (d) => {
    if (!window.confirm(`Supprimer « ${d.title} » ?`)) return;
    try {
      await api.delete(`/documents/${d.id}`);
      toast.success("Document supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const toggleArchive = async (d) => {
    try {
      await api.post(`/documents/${d.id}/${d.is_archived ? "unarchive" : "archive"}`);
      toast.success(d.is_archived ? "Document désarchivé" : "Document archivé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const saveEdit = async () => {
    try {
      await api.put(`/documents/${editDoc.id}`, {
        title: editDoc.title,
        description: editDoc.description,
        folder_id: editDoc.folder_id === "none" ? null : editDoc.folder_id,
        tags: (editDoc.tagsStr || "").split(",").map((t) => t.trim()).filter(Boolean),
      });
      toast.success("Document mis à jour");
      setEditDoc(null);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const saveShare = async () => {
    try {
      await api.post(`/documents/${shareDoc.id}/share`, { user_ids: shareSelected });
      toast.success("Partage mis à jour");
      setShareDoc(null);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const openComments = async (d) => {
    setCommentsDoc(d);
    setCommentDraft("");
    try {
      const { data } = await api.get(`/documents/${d.id}/comments`);
      setComments(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const sendComment = async (e) => {
    e?.preventDefault?.();
    if (!commentDraft.trim()) return;
    try {
      await api.post(`/documents/${commentsDoc.id}/comments`, { content: commentDraft });
      setCommentDraft("");
      const { data } = await api.get(`/documents/${commentsDoc.id}/comments`);
      setComments(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const removeComment = async (cid) => {
    try {
      await api.delete(`/comments/${cid}`);
      setComments(comments.filter((c) => c.id !== cid));
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <div className="space-y-6" data-testid="documents-page">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            {archivedView ? "Archives" : "Bibliothèque"}
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            {archivedView ? "Documents archivés" : "Documents"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {docs.length} document{docs.length > 1 ? "s" : ""}
          </p>
        </div>
        {!archivedView && (
          <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
            <DialogTrigger asChild>
              <Button className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="upload-btn">
                <Upload size={16} className="mr-2" /> Importer un document
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle style={{ fontFamily: "Work Sans" }}>Nouveau document</DialogTitle>
                <DialogDescription>Téléversez un document dans la GED.</DialogDescription>
              </DialogHeader>
              <form onSubmit={onUpload} className="space-y-4" data-testid="upload-form">
                <div>
                  <Label>Fichier *</Label>
                  <Input type="file" onChange={(e) => setFile(e.target.files[0])} data-testid="upload-file" />
                </div>
                <div>
                  <Label>Titre *</Label>
                  <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required data-testid="upload-title" />
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="upload-desc" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Dossier</Label>
                    <Select value={form.folder_id} onValueChange={(v) => setForm({ ...form, folder_id: v })}>
                      <SelectTrigger data-testid="upload-folder"><SelectValue placeholder="Aucun" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Aucun</SelectItem>
                        {folders.map((f) => <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Tags (séparés par virgule)</Label>
                    <Input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="ex: contrat, 2026" data-testid="upload-tags" />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setUploadOpen(false)}>Annuler</Button>
                  <Button type="submit" disabled={uploading} className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="upload-submit">
                    {uploading ? "Envoi..." : "Téléverser"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="inst-card p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input placeholder="Rechercher un document..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="doc-search" />
        </div>
        <Select value={filterFolder} onValueChange={setFilterFolder}>
          <SelectTrigger className="w-[200px]" data-testid="doc-filter-folder"><SelectValue placeholder="Tous dossiers" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les dossiers</SelectItem>
            {folders.map((f) => <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={filterTag} onValueChange={setFilterTag}>
          <SelectTrigger className="w-[180px]" data-testid="doc-filter-tag"><SelectValue placeholder="Tous tags" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les tags</SelectItem>
            {tags.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="inst-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 hover:bg-gray-50">
              <TableHead>Document</TableHead>
              <TableHead>Dossier</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead>Taille</TableHead>
              <TableHead>Importé par</TableHead>
              <TableHead>Date</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={7} className="text-center text-gray-500 py-8">Chargement...</TableCell></TableRow>
            ) : docs.length === 0 ? (
              <TableRow><TableCell colSpan={7} className="text-center text-gray-500 py-10">Aucun document.</TableCell></TableRow>
            ) : docs.map((d) => (
              <TableRow key={d.id} data-testid={`doc-row-${d.id}`}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-100 text-gray-500 rounded flex items-center justify-center"><FileText size={14} /></div>
                    <div className="min-w-0">
                      <div className="font-medium text-gray-900 truncate max-w-[260px]">{d.title}</div>
                      <div className="text-xs text-gray-500 truncate max-w-[260px]">{d.original_filename}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-gray-600">{d.folder_name || "—"}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1 max-w-[180px]">
                    {(d.tags || []).slice(0, 3).map((t) => <Badge key={t} variant="secondary" className="bg-[#e8f3ed] text-[#0f4c3a] hover:bg-[#e8f3ed]">{t}</Badge>)}
                  </div>
                </TableCell>
                <TableCell className="text-gray-600">{formatBytes(d.size)}</TableCell>
                <TableCell className="text-gray-600">{d.uploaded_by_name || "—"}</TableCell>
                <TableCell className="text-gray-600 whitespace-nowrap">{formatDate(d.created_at)}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" data-testid={`doc-menu-${d.id}`}><MoreVertical size={16} /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => downloadDoc(d)} data-testid={`download-${d.id}`}><Download size={14} className="mr-2" />Télécharger</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setEditDoc({ ...d, tagsStr: (d.tags || []).join(", "), folder_id: d.folder_id || "none" })}><Pencil size={14} className="mr-2" />Modifier</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => openComments(d)} data-testid={`comments-${d.id}`}><MessageSquare size={14} className="mr-2" />Commentaires</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleArchive(d)}><Archive size={14} className="mr-2" />{d.is_archived ? "Désarchiver" : "Archiver"}</DropdownMenuItem>
                      {(user?.role === "admin" || d.uploaded_by === user?.id) && (
                        <>
                          <DropdownMenuItem onClick={() => { setShareDoc(d); setShareSelected(d.shared_with || []); }}><Share2 size={14} className="mr-2" />Partager</DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => deleteDoc(d)} className="text-red-600"><Trash2 size={14} className="mr-2" />Supprimer</DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Edit Dialog */}
      <Dialog open={!!editDoc} onOpenChange={(o) => !o && setEditDoc(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader><DialogTitle>Modifier le document</DialogTitle></DialogHeader>
          {editDoc && (
            <div className="space-y-3">
              <div><Label>Titre</Label><Input value={editDoc.title} onChange={(e) => setEditDoc({ ...editDoc, title: e.target.value })} /></div>
              <div><Label>Description</Label><Textarea value={editDoc.description || ""} onChange={(e) => setEditDoc({ ...editDoc, description: e.target.value })} /></div>
              <div>
                <Label>Dossier</Label>
                <Select value={editDoc.folder_id} onValueChange={(v) => setEditDoc({ ...editDoc, folder_id: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Aucun</SelectItem>
                    {folders.map((f) => <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div><Label>Tags (séparés par virgule)</Label><Input value={editDoc.tagsStr} onChange={(e) => setEditDoc({ ...editDoc, tagsStr: e.target.value })} /></div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDoc(null)}>Annuler</Button>
            <Button onClick={saveEdit} className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white">Enregistrer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={!!shareDoc} onOpenChange={(o) => !o && setShareDoc(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Partager « {shareDoc?.title} »</DialogTitle>
            <DialogDescription>Sélectionnez les agents qui auront accès à ce document.</DialogDescription>
          </DialogHeader>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {agents.length === 0 && <div className="text-sm text-gray-500">Aucun autre agent disponible. Vous pouvez en créer depuis la page Agents.</div>}
            {agents.map((a) => {
              const checked = shareSelected.includes(a.id);
              return (
                <label key={a.id} className="flex items-center gap-3 p-2 rounded hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(e) => {
                      if (e.target.checked) setShareSelected([...shareSelected, a.id]);
                      else setShareSelected(shareSelected.filter((x) => x !== a.id));
                    }}
                  />
                  <div>
                    <div className="text-sm font-medium">{a.name}</div>
                    <div className="text-xs text-gray-500">{a.email} · {a.role}</div>
                  </div>
                </label>
              );
            })}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShareDoc(null)}>Annuler</Button>
            <Button onClick={saveShare} className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white">Enregistrer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comments Dialog */}
      <Dialog open={!!commentsDoc} onOpenChange={(o) => { if (!o) { setCommentsDoc(null); setComments([]); } }}>
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Discussion · {commentsDoc?.title}</DialogTitle>
            <DialogDescription>
              Échangez des notes avec les agents qui ont accès à ce document.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 max-h-[400px] overflow-y-auto py-2" data-testid="comments-list">
            {comments.length === 0 && (
              <div className="text-center text-sm text-gray-500 py-6">
                <MessageSquare size={28} className="mx-auto text-gray-300 mb-2" />
                Aucun commentaire pour l'instant.
              </div>
            )}
            {comments.map((c) => {
              const mine = c.user_id === user?.id;
              const canDelete = mine || user?.role === "admin";
              return (
                <div key={c.id} className={`flex ${mine ? "justify-end" : "justify-start"}`} data-testid={`comment-${c.id}`}>
                  <div className={`max-w-[80%] rounded-lg px-3 py-2 ${mine ? "bg-[#0f4c3a] text-white" : "bg-gray-100 text-gray-900"}`}>
                    <div className={`text-xs font-semibold mb-0.5 ${mine ? "text-white/80" : "text-[#0f4c3a]"}`}>{c.user_name}</div>
                    <div className="text-sm whitespace-pre-wrap">{c.content}</div>
                    <div className={`text-[10px] mt-1 flex items-center justify-between gap-2 ${mine ? "text-white/60" : "text-gray-500"}`}>
                      <span>{formatDate(c.created_at)}</span>
                      {canDelete && (
                        <button
                          onClick={() => removeComment(c.id)}
                          className={`hover:underline ${mine ? "text-white/80" : "text-red-600"}`}
                          data-testid={`comment-delete-${c.id}`}
                        >
                          Supprimer
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <form onSubmit={sendComment} className="flex gap-2 pt-3 border-t border-gray-100">
            <Input
              value={commentDraft}
              onChange={(e) => setCommentDraft(e.target.value)}
              placeholder="Écrire un commentaire..."
              data-testid="comment-input"
            />
            <Button type="submit" className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="comment-submit">
              <Send size={14} />
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
