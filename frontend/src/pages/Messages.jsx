import React, { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import {
  MessageSquare, Send, Paperclip, X, Inbox, Search, Trash2, Check, CheckCheck, Users, Plus,
} from "lucide-react";

function getInitials(name = "") {
  return name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase() || "?";
}

export default function Messages() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [agents, setAgents] = useState([]);
  const [docs, setDocs] = useState([]);
  const [search, setSearch] = useState("");
  const [activePeer, setActivePeer] = useState(null);
  const [thread, setThread] = useState([]);
  const [threadSearch, setThreadSearch] = useState("");
  const [draft, setDraft] = useState("");
  const [attachId, setAttachId] = useState("none");
  const [sending, setSending] = useState(false);
  const [newRecipient, setNewRecipient] = useState("");

  // Broadcast dialog state
  const [broadcastOpen, setBroadcastOpen] = useState(false);
  const [broadcastSelected, setBroadcastSelected] = useState([]);
  const [broadcastContent, setBroadcastContent] = useState("");
  const [broadcastAttach, setBroadcastAttach] = useState("none");
  const [broadcastSending, setBroadcastSending] = useState(false);

  const bottomRef = useRef(null);

  const loadConversations = useCallback(async () => {
    try {
      const params = search.trim() ? { search: search.trim() } : {};
      const { data } = await api.get("/messages/conversations", { params });
      setConversations(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, [search]);

  const loadThread = useCallback(async (peerId, query = "") => {
    try {
      const params = query.trim() ? { search: query.trim() } : {};
      const { data } = await api.get(`/messages/conversation/${peerId}`, { params });
      setActivePeer(data.peer);
      setThread(data.messages);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
      loadConversations();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, [loadConversations]);

  useEffect(() => {
    loadConversations();
    api.get("/users").then((r) => setAgents(r.data.filter((u) => u.id !== user?.id))).catch(() => {});
    api.get("/documents").then((r) => setDocs(r.data)).catch(() => {});
    const i = setInterval(loadConversations, 30000);
    return () => clearInterval(i);
  }, [loadConversations, user]);

  // Refresh active thread on a separate timer for "near real-time" feel
  useEffect(() => {
    if (!activePeer) return;
    const i = setInterval(() => {
      api.get(`/messages/conversation/${activePeer.id}`)
        .then((r) => setThread(r.data.messages))
        .catch(() => {});
    }, 10000);
    return () => clearInterval(i);
  }, [activePeer]);

  const send = async (e) => {
    e?.preventDefault?.();
    if (!activePeer) return;
    if (!draft.trim() && attachId === "none") return;
    setSending(true);
    try {
      const payload = { to_user_id: activePeer.id, content: draft.trim() };
      if (attachId && attachId !== "none") payload.attachment_doc_id = attachId;
      await api.post("/messages", payload);
      setDraft("");
      setAttachId("none");
      loadThread(activePeer.id, threadSearch);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSending(false);
    }
  };

  const deleteMessage = async (m) => {
    if (!window.confirm("Supprimer ce message ?")) return;
    try {
      await api.delete(`/messages/${m.id}`);
      toast.success("Message supprimé");
      loadThread(activePeer.id, threadSearch);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const startNew = (peerId) => {
    if (!peerId) return;
    loadThread(peerId);
    setNewRecipient("");
  };

  const toggleBroadcastRecipient = (id) => {
    setBroadcastSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const sendBroadcast = async (e) => {
    e?.preventDefault?.();
    if (!broadcastContent.trim() && broadcastAttach === "none") {
      toast.error("Veuillez écrire un message");
      return;
    }
    if (broadcastSelected.length === 0) {
      toast.error("Sélectionnez au moins un destinataire");
      return;
    }
    setBroadcastSending(true);
    try {
      const payload = {
        to_user_ids: broadcastSelected,
        content: broadcastContent.trim(),
      };
      if (broadcastAttach !== "none") payload.attachment_doc_id = broadcastAttach;
      const { data } = await api.post("/messages/broadcast", payload);
      toast.success(`Message envoyé à ${data.sent} destinataire(s)`);
      setBroadcastOpen(false);
      setBroadcastSelected([]);
      setBroadcastContent("");
      setBroadcastAttach("none");
      loadConversations();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBroadcastSending(false);
    }
  };

  const recipientOptions = useMemo(() => agents, [agents]);

  return (
    <div className="space-y-4" data-testid="messages-page">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            Communication
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            Messagerie
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Échangez en privé, partagez des documents, diffusez à plusieurs agents
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Dialog open={broadcastOpen} onOpenChange={(o) => { setBroadcastOpen(o); if (!o) { setBroadcastSelected([]); setBroadcastContent(""); setBroadcastAttach("none"); } }}>
            <DialogTrigger asChild>
              <Button variant="outline" data-testid="broadcast-btn">
                <Users size={16} className="mr-2" /> Diffuser à plusieurs
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>Diffuser un message</DialogTitle>
                <DialogDescription>
                  Envoyez le même message à plusieurs agents. Si vous joignez un document, ils y auront automatiquement accès.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={sendBroadcast} className="space-y-3" data-testid="broadcast-form">
                <div>
                  <div className="text-xs font-medium text-gray-700 mb-1.5">Destinataires ({broadcastSelected.length})</div>
                  <div className="max-h-48 overflow-y-auto border border-gray-200 rounded p-2 space-y-1">
                    {recipientOptions.length === 0 && <div className="text-xs text-gray-500 px-2 py-3">Aucun autre agent.</div>}
                    {recipientOptions.map((a) => {
                      const checked = broadcastSelected.includes(a.id);
                      return (
                        <label key={a.id} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-50 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleBroadcastRecipient(a.id)}
                            data-testid={`broadcast-check-${a.id}`}
                          />
                          <span className="text-sm">{a.name}</span>
                          <span className="text-xs text-gray-500 capitalize">· {a.role}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
                <div>
                  <Textarea
                    placeholder="Votre message..."
                    value={broadcastContent}
                    onChange={(e) => setBroadcastContent(e.target.value)}
                    rows={4}
                    data-testid="broadcast-content"
                  />
                </div>
                <div>
                  <div className="text-xs font-medium text-gray-700 mb-1.5">Pièce jointe</div>
                  <Select value={broadcastAttach} onValueChange={setBroadcastAttach}>
                    <SelectTrigger data-testid="broadcast-attach"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sans pièce jointe</SelectItem>
                      {docs.slice(0, 50).map((d) => <SelectItem key={d.id} value={d.id}>{d.title}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setBroadcastOpen(false)}>Annuler</Button>
                  <Button
                    type="submit"
                    disabled={broadcastSending}
                    className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white"
                    data-testid="broadcast-submit"
                  >
                    {broadcastSending ? "Envoi..." : `Envoyer à ${broadcastSelected.length}`}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          <div className="w-56">
            <Select value={newRecipient} onValueChange={(v) => { setNewRecipient(v); startNew(v); }}>
              <SelectTrigger data-testid="msg-new-recipient">
                <SelectValue placeholder="Nouveau message à..." />
              </SelectTrigger>
              <SelectContent>
                {agents.map((a) => (
                  <SelectItem key={a.id} value={a.id}>{a.name} · {a.role}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 h-[calc(100vh-220px)] min-h-[500px]">
        {/* Conversation list */}
        <div className="inst-card overflow-hidden flex flex-col">
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Rechercher..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 h-9 text-sm"
                data-testid="conv-search"
              />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="conv-list">
            {conversations.length === 0 ? (
              <div className="text-sm text-gray-500 p-8 text-center">
                <MessageSquare size={28} className="mx-auto text-gray-300 mb-2" />
                {search.trim() ? "Aucun résultat." : "Aucune conversation."}
              </div>
            ) : (
              <ul>
                {conversations.map((c) => {
                  const isActive = activePeer?.id === c.peer.id;
                  return (
                    <li
                      key={c.peer.id}
                      onClick={() => loadThread(c.peer.id)}
                      className={`px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${isActive ? "bg-[#e8f3ed]" : ""}`}
                      data-testid={`conv-${c.peer.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9">
                          <AvatarFallback className="bg-[#0f4c3a] text-white text-xs">
                            {getInitials(c.peer.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <div className="font-medium text-gray-900 truncate">{c.peer.name}</div>
                            {c.unread_count > 0 && (
                              <span className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-[#dc241f] text-white text-[10px] font-semibold">
                                {c.unread_count}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {c.last_message.from_user_id === user?.id ? "Vous : " : ""}
                            {c.last_message.content || "[pièce jointe]"}
                          </div>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>

        {/* Thread */}
        <div className="inst-card flex flex-col overflow-hidden">
          {!activePeer ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <Inbox size={48} className="text-gray-300 mb-3" />
              <div className="text-sm">Sélectionnez une conversation pour afficher les messages</div>
            </div>
          ) : (
            <>
              <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-3">
                <Avatar className="h-9 w-9">
                  <AvatarFallback className="bg-[#0f4c3a] text-white text-xs">
                    {getInitials(activePeer.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900">{activePeer.name}</div>
                  <div className="text-xs text-gray-500">{activePeer.email}</div>
                </div>
                <div className="relative w-48">
                  <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                  <Input
                    placeholder="Chercher dans cette conv..."
                    value={threadSearch}
                    onChange={(e) => {
                      setThreadSearch(e.target.value);
                      loadThread(activePeer.id, e.target.value);
                    }}
                    className="pl-7 h-8 text-xs"
                    data-testid="thread-search"
                  />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-[#fafbf7]" data-testid="msg-thread">
                {thread.length === 0 && (
                  <div className="text-center text-sm text-gray-500">
                    {threadSearch ? "Aucun résultat." : "Aucun message — écrivez le premier !"}
                  </div>
                )}
                {thread.map((m) => {
                  const mine = m.from_user_id === user?.id;
                  return (
                    <div key={m.id} className={`flex group ${mine ? "justify-end" : "justify-start"}`}>
                      <div className={`relative max-w-[70%] rounded-2xl px-4 py-2 shadow-sm ${mine ? "bg-[#0f4c3a] text-white" : "bg-white border border-gray-200 text-gray-900"}`}>
                        {m.content && <div className="text-sm whitespace-pre-wrap">{m.content}</div>}
                        {m.attachment && (
                          <div className={`mt-1 text-xs flex items-center gap-1 ${mine ? "text-white/85" : "text-[#0f4c3a]"}`}>
                            <Paperclip size={12} /> {m.attachment.title}
                          </div>
                        )}
                        <div className={`flex items-center gap-1.5 mt-1 text-[10px] ${mine ? "text-white/60 justify-end" : "text-gray-400"}`}>
                          <span>{formatDate(m.created_at)}</span>
                          {mine && (m.is_read ? (
                            <CheckCheck size={11} className="text-white" data-testid={`msg-read-${m.id}`} />
                          ) : (
                            <Check size={11} className="text-white/60" data-testid={`msg-sent-${m.id}`} />
                          ))}
                        </div>
                        {mine && (
                          <button
                            onClick={() => deleteMessage(m)}
                            className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-white border border-gray-200 text-red-600 rounded-full w-6 h-6 flex items-center justify-center shadow-sm hover:bg-red-50"
                            title="Supprimer"
                            data-testid={`msg-delete-${m.id}`}
                          >
                            <Trash2 size={11} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>
              <form onSubmit={send} className="p-3 border-t border-gray-100 space-y-2" data-testid="msg-form">
                {attachId !== "none" && (
                  <div className="text-xs flex items-center gap-2 text-[#0f4c3a] bg-[#e8f3ed] rounded px-2 py-1 w-fit">
                    <Paperclip size={12} />
                    {docs.find((d) => d.id === attachId)?.title || "Document"}
                    <button type="button" onClick={() => setAttachId("none")} className="hover:text-red-600">
                      <X size={12} />
                    </button>
                  </div>
                )}
                <div className="flex items-end gap-2">
                  <Textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Écrivez votre message..."
                    className="min-h-[44px] resize-none"
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(e); } }}
                    data-testid="msg-input"
                  />
                  <Select value={attachId} onValueChange={setAttachId}>
                    <SelectTrigger className="w-[44px] h-11 p-0 flex items-center justify-center" title="Joindre un document">
                      <Paperclip size={16} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sans pièce jointe</SelectItem>
                      {docs.slice(0, 50).map((d) => (
                        <SelectItem key={d.id} value={d.id}>{d.title}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="submit"
                    disabled={sending}
                    className="bg-[#0f4c3a] hover:bg-[#1a6b53] text-white h-11"
                    data-testid="msg-send"
                  >
                    <Send size={14} className="mr-1" />
                    {sending ? "..." : "Envoyer"}
                  </Button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
