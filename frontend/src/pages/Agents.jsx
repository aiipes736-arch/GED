import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Badge } from "../components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger, DialogDescription,
} from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator,
} from "../components/ui/dropdown-menu";
import { UserPlus, MoreVertical, Pencil, Trash2, Key } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { Navigate } from "react-router-dom";

export default function Agents() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ email: "", password: "", name: "", role: "agent" });
  const [resetTarget, setResetTarget] = useState(null);
  const [resetPwd, setResetPwd] = useState("");
  const [resetPwd2, setResetPwd2] = useState("");

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/users");
      setUsers(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, []);

  useEffect(() => { if (user?.role === "admin") load(); }, [load, user]);

  if (user && user.role !== "admin") return <Navigate to="/" replace />;

  const save = async (e) => {
    e?.preventDefault?.();
    try {
      if (edit) {
        const payload = { name: form.name, role: form.role };
        if (form.password) payload.password = form.password;
        await api.put(`/users/${edit.id}`, payload);
        toast.success("Agent mis à jour");
      } else {
        await api.post("/users", form);
        toast.success("Agent créé");
      }
      setOpen(false);
      setEdit(null);
      setForm({ email: "", password: "", name: "", role: "agent" });
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const toggleActive = async (u) => {
    try {
      await api.put(`/users/${u.id}`, { is_active: !u.is_active });
      toast.success(u.is_active ? "Agent désactivé" : "Agent activé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const remove = async (u) => {
    if (!window.confirm(`Supprimer l'agent « ${u.name} » ?`)) return;
    try {
      await api.delete(`/users/${u.id}`);
      toast.success("Agent supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const submitReset = async (e) => {
    e?.preventDefault?.();
    if (resetPwd.length < 6) {
      toast.error("Mot de passe trop court (min 6 caractères)");
      return;
    }
    if (resetPwd !== resetPwd2) {
      toast.error("Les deux mots de passe ne correspondent pas");
      return;
    }
    try {
      await api.post(`/users/${resetTarget.id}/reset-password`, { new_password: resetPwd });
      toast.success(`Mot de passe réinitialisé pour ${resetTarget.name}`);
      setResetTarget(null);
      setResetPwd("");
      setResetPwd2("");
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  return (
    <div className="space-y-6" data-testid="agents-page">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Administration</div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>Agents</h1>
          <p className="text-sm text-gray-500 mt-1">{users.length} utilisateur{users.length > 1 ? "s" : ""} enregistré{users.length > 1 ? "s" : ""}</p>
        </div>
        <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) { setEdit(null); setForm({ email: "", password: "", name: "", role: "agent" }); } }}>
          <DialogTrigger asChild>
            <Button className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="new-agent-btn" onClick={() => { setEdit(null); setForm({ email: "", password: "", name: "", role: "agent" }); }}>
              <UserPlus size={16} className="mr-2" /> Nouvel agent
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{edit ? "Modifier l'agent" : "Nouvel agent"}</DialogTitle>
              <DialogDescription>{edit ? "Mettre à jour les informations de l'agent." : "Créer un nouveau compte pour un agent."}</DialogDescription>
            </DialogHeader>
            <form onSubmit={save} className="space-y-3">
              <div><Label>Nom complet *</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required data-testid="agent-name" /></div>
              {!edit && (
                <div><Label>Email *</Label><Input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required data-testid="agent-email" /></div>
              )}
              <div>
                <Label>{edit ? "Nouveau mot de passe (optionnel)" : "Mot de passe *"}</Label>
                <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required={!edit} data-testid="agent-password" />
              </div>
              <div>
                <Label>Rôle *</Label>
                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                  <SelectTrigger data-testid="agent-role"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="agent">Agent</SelectItem>
                    <SelectItem value="admin">Administrateur</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Annuler</Button>
                <Button type="submit" className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white" data-testid="agent-submit">Enregistrer</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="inst-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 hover:bg-gray-50">
              <TableHead>Agent</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rôle</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Créé le</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} data-testid={`agent-row-${u.id}`}>
                <TableCell className="font-medium">{u.name}</TableCell>
                <TableCell className="text-gray-600">{u.email}</TableCell>
                <TableCell>
                  <Badge className={u.role === "admin" ? "bg-[#e8f3ed] text-[#0f4c3a] hover:bg-[#e8f3ed]" : "bg-gray-100 text-gray-700 hover:bg-gray-100"}>
                    {u.role === "admin" ? "Administrateur" : "Agent"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Switch checked={u.is_active} onCheckedChange={() => toggleActive(u)} disabled={u.id === user.id} data-testid={`agent-toggle-${u.id}`} />
                    <span className={`text-xs ${u.is_active ? "text-green-700" : "text-gray-500"}`}>{u.is_active ? "Actif" : "Désactivé"}</span>
                  </div>
                </TableCell>
                <TableCell className="text-gray-600">{formatDate(u.created_at)}</TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon"><MoreVertical size={16} /></Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => { setEdit(u); setForm({ email: u.email, password: "", name: u.name, role: u.role }); setOpen(true); }} data-testid={`agent-edit-${u.id}`}>
                        <Pencil size={14} className="mr-2" /> Modifier
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setResetTarget(u)} data-testid={`agent-reset-${u.id}`}>
                        <Key size={14} className="mr-2" /> Réinitialiser le mot de passe
                      </DropdownMenuItem>
                      {u.id !== user.id && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => remove(u)} className="text-red-600" data-testid={`agent-delete-${u.id}`}>
                            <Trash2 size={14} className="mr-2" /> Supprimer
                          </DropdownMenuItem>
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

      {/* Reset password dialog */}
      <Dialog open={!!resetTarget} onOpenChange={(o) => { if (!o) { setResetTarget(null); setResetPwd(""); setResetPwd2(""); } }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Réinitialiser le mot de passe</DialogTitle>
            <DialogDescription>
              Vous êtes sur le point de définir un nouveau mot de passe pour <span className="font-semibold text-gray-900">{resetTarget?.name}</span> ({resetTarget?.email}). L'agent sera notifié dans son espace.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={submitReset} className="space-y-3" data-testid="reset-password-form">
            <div>
              <Label>Nouveau mot de passe *</Label>
              <Input
                type="password"
                value={resetPwd}
                onChange={(e) => setResetPwd(e.target.value)}
                required
                minLength={6}
                data-testid="reset-password-input"
              />
            </div>
            <div>
              <Label>Confirmation *</Label>
              <Input
                type="password"
                value={resetPwd2}
                onChange={(e) => setResetPwd2(e.target.value)}
                required
                minLength={6}
                data-testid="reset-password-confirm"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setResetTarget(null)}>Annuler</Button>
              <Button
                type="submit"
                className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
                data-testid="reset-password-submit"
              >
                Réinitialiser
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
