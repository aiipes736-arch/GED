import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Check, CheckCheck } from "lucide-react";
import api, { formatDate } from "../lib/api";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
} from "./ui/dropdown-menu";
import { useAuth } from "../contexts/AuthContext";

export default function Header() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState({ items: [], unread_count: 0 });
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/notifications");
      setData(data);
    } catch (err) {
      console.error("Header.loadNotifications failed:", err);
    }
  }, []);

  useEffect(() => {
    if (user) {
      load();
      const id = setInterval(load, 30000); // poll every 30s
      return () => clearInterval(id);
    }
  }, [load, user]);

  const onItemClick = async (n) => {
    if (!n.is_read) {
      try {
        await api.post(`/notifications/${n.id}/read`);
      } catch (err) {
        console.error("Header.markRead failed:", err);
      }
      load();
    }
    if (n.link) {
      setOpen(false);
      navigate(n.link);
    }
  };

  const markAll = async () => {
    try {
      await api.post("/notifications/read-all");
      load();
    } catch (err) {
      console.error("Header.markAll failed:", err);
    }
  };

  return (
    <div className="flex items-center justify-end gap-2 mb-2" data-testid="app-header">
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="relative"
            data-testid="notif-bell"
            aria-label="Notifications"
          >
            <Bell size={18} />
            {data.unread_count > 0 && (
              <span
                className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-[#dc241f] text-white text-[10px] font-semibold flex items-center justify-center px-1"
                data-testid="notif-badge"
              >
                {data.unread_count > 99 ? "99+" : data.unread_count}
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[360px] p-0" data-testid="notif-dropdown">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <div className="font-semibold text-gray-900" style={{ fontFamily: "Work Sans" }}>
              Notifications
            </div>
            {data.unread_count > 0 && (
              <button
                onClick={markAll}
                className="text-xs text-[#0f4c3a] hover:underline flex items-center gap-1"
                data-testid="notif-mark-all"
              >
                <CheckCheck size={12} /> Tout marquer comme lu
              </button>
            )}
          </div>
          <div className="max-h-[420px] overflow-y-auto">
            {data.items.length === 0 ? (
              <div className="px-4 py-10 text-center text-sm text-gray-500">
                Aucune notification pour le moment.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {data.items.map((n) => (
                  <li
                    key={n.id}
                    onClick={() => onItemClick(n)}
                    className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${
                      !n.is_read ? "bg-[#f0fdf4]" : ""
                    }`}
                    data-testid={`notif-item-${n.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={`w-2 h-2 mt-2 rounded-full flex-shrink-0 ${
                          n.is_read ? "bg-gray-300" : "bg-[#0f4c3a]"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {n.title}
                        </div>
                        <div className="text-xs text-gray-600 mt-0.5 line-clamp-2">
                          {n.message}
                        </div>
                        <div className="text-[11px] text-gray-400 mt-1">
                          {formatDate(n.created_at)}
                        </div>
                      </div>
                      {!n.is_read && (
                        <Check size={14} className="text-[#0f4c3a] mt-1" />
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
