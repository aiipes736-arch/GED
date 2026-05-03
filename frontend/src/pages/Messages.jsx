import React, { useEffect, useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import api, { formatApiError, formatDate } from "../lib/api";
import { useAuth } from "../contexts/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { MessageSquare, Send, Paperclip, X, Inbox } from "lucide-react";

function getInitials(name = "") {
  return name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase() || "?";
}

export default function Messages() {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [agents, setAgents] = useState([]);
  const [docs, setDocs] = useState([]);
  const [activePeer, setActivePeer] = useState(null); // {id, name, email, role}
  const [thread, setThread] = useState([]);
  const [draft, setDraft] = useState("");
  const [attachId, setAttachId] = useState("none");
  const [sending, setSending] = useState(false);
  const [newRecipient, setNewRecipient] = useState("");
  const bottomRef = useRef(null);

  const loadConversations = useCallback(async () => {
    try {
      const { data } = await api.get("/messages/conversations");
      setConversations(data);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  }, []);

  const loadThread = useCallback(async (peerId) => {
    try {
      const { data } = await api.get(`/messages/conversation/${peerId}`);
      setActivePeer(data.peer);
      setThread(data.messages);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
      loadConversations(); // refresh unread counts
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

  const send = async (e) => {
    e?.preventDefault?.();
    if (!activePeer) return;
    if (!draft.trim() && attachId === "none") return;
    setSending(true);
    try {
      const payload = {
        to_user_id: activePeer.id,
        content: draft.trim(),
      };
      if (attachId && attachId !== "none") payload.attachment_doc_id = attachId;
      await api.post("/messages", payload);
      setDraft("");
      setAttachId("none");
      loadThread(activePeer.id);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSending(false);
    }
  };

  const startNew = (peerId) => {
    if (!peerId) return;
    const a = agents.find((x) => x.id === peerId);
    if (a) loadThread(peerId);
    setNewRecipient("");
  };

  return (
    <div className="space-y-4" data-testid="messages-page">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">
            Communication
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>
            Messagerie
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Échangez en privé avec d'autres agents et joignez des documents de la GED
          </p>
        </div>
        <div className="w-64">
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

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-4 h-[calc(100vh-220px)] min-h-[500px]">
        {/* Conversation list */}
        <div className="inst-card overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-gray-100 text-[11px] uppercase tracking-wider text-gray-500 font-semibold">
            Conversations ({conversations.length})
          </div>
          <div className="flex-1 overflow-y-auto" data-testid="conv-list">
            {conversations.length === 0 ? (
              <div className="text-sm text-gray-500 p-8 text-center">
                <MessageSquare size={28} className="mx-auto text-gray-300 mb-2" />
                Aucune conversation. Démarrez-en une via le sélecteur ci-dessus.
              </div>
            ) : (
              <ul>
                {conversations.map((c) => {
                  const isActive = activePeer?.id === c.peer.id;
                  return (
                    <li
                      key={c.peer.id}
                      onClick={() => loadThread(c.peer.id)}
                      className={`px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-gray-50 ${
                        isActive ? "bg-[#e8f3ed]" : ""
                      }`}
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
                <div>
                  <div className="font-semibold text-gray-900">{activePeer.name}</div>
                  <div className="text-xs text-gray-500">{activePeer.email}</div>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-[#fafbf7]" data-testid="msg-thread">
                {thread.length === 0 && (
                  <div className="text-center text-sm text-gray-500">Aucun message — écrivez le premier !</div>
                )}
                {thread.map((m) => {
                  const mine = m.from_user_id === user?.id;
                  return (
                    <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-2 shadow-sm ${
                          mine ? "bg-[#0f4c3a] text-white" : "bg-white border border-gray-200 text-gray-900"
                        }`}
                      >
                        {m.content && <div className="text-sm whitespace-pre-wrap">{m.content}</div>}
                        {m.attachment && (
                          <div className={`mt-1 text-xs flex items-center gap-1 ${mine ? "text-white/80" : "text-[#0f4c3a]"}`}>
                            <Paperclip size={12} /> {m.attachment.title}
                          </div>
                        )}
                        <div className={`text-[10px] mt-1 ${mine ? "text-white/60" : "text-gray-400"}`}>
                          {formatDate(m.created_at)}
                        </div>
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
