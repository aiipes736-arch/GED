import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  Users,
  Archive,
  History,
  LogOut,
  Shield,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { LOGO_URL } from "../lib/api";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback } from "./ui/avatar";

const items = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard, exact: true, testId: "nav-dashboard" },
  { to: "/documents", label: "Documents", icon: FileText, testId: "nav-documents" },
  { to: "/folders", label: "Dossiers", icon: FolderOpen, testId: "nav-folders" },
  { to: "/archive", label: "Archives", icon: Archive, testId: "nav-archive" },
  { to: "/activity", label: "Journal d'activité", icon: History, testId: "nav-activity" },
  { to: "/agents", label: "Agents", icon: Users, adminOnly: true, testId: "nav-agents" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === "admin";

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  const initials = (user?.name || user?.email || "U")
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <aside className="hidden lg:flex w-64 flex-col bg-white border-r border-gray-200 min-h-screen" data-testid="sidebar">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-200">
        <img src={LOGO_URL} alt="MHCGED" className="w-11 h-11 rounded-md object-cover" data-testid="sidebar-logo" />
        <div>
          <div className="font-bold text-gray-900 leading-none tracking-tight" style={{ fontFamily: "Work Sans" }}>MHCGED</div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-gray-500 mt-1">Ministère des Hydrocarbures</div>
        </div>
      </div>

      <div className="h-1 flag-bar" />

      <nav className="flex-1 p-3 space-y-1">
        {items.map((it) => {
          if (it.adminOnly && !isAdmin) return null;
          const Icon = it.icon;
          return (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.exact}
              data-testid={it.testId}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              <Icon size={18} strokeWidth={2} />
              <span>{it.label}</span>
              {it.adminOnly && (
                <span className="ml-auto inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">
                  <Shield size={10} /> Admin
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-gray-200 p-3">
        <NavLink to="/profile" className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50" data-testid="nav-profile">
          <Avatar className="h-9 w-9">
            <AvatarFallback className="bg-[#0f4c3a] text-white text-xs font-semibold">{initials}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <div className="text-sm font-medium text-gray-900 truncate">{user?.name || user?.email}</div>
            <div className="text-xs text-gray-500 capitalize">{user?.role === "admin" ? "Administrateur" : "Agent"}</div>
          </div>
        </NavLink>
        <Button
          onClick={onLogout}
          variant="ghost"
          className="w-full justify-start mt-2 text-gray-600 hover:text-red-600 hover:bg-red-50"
          data-testid="logout-btn"
        >
          <LogOut size={16} className="mr-2" />
          Se déconnecter
        </Button>
      </div>
    </aside>
  );
}
