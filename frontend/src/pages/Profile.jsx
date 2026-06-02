import React from "react";
import { useAuth } from "../contexts/AuthContext";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { formatDate } from "../lib/api";

export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;
  const initials = (user.name || user.email).split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div className="space-y-6" data-testid="profile-page">
      <div>
        <div className="text-[11px] uppercase tracking-[0.25em] text-[#0f4c3a] font-semibold">Compte</div>
        <h1 className="text-3xl sm:text-4xl font-bold mt-1 text-gray-900" style={{ fontFamily: "Work Sans" }}>Mon profil</h1>
      </div>
      <div className="inst-card p-8 flex items-center gap-6">
        <Avatar className="h-20 w-20">
          <AvatarFallback className="bg-[#0f4c3a] text-white text-xl font-semibold">{initials}</AvatarFallback>
        </Avatar>
        <div>
          <div className="text-2xl font-bold text-gray-900" style={{ fontFamily: "Work Sans" }}>{user.name}</div>
          <div className="text-gray-500">{user.email}</div>
          <div className="mt-2 inline-block text-[11px] uppercase tracking-wider font-semibold bg-[#e8f3ed] text-[#0f4c3a] px-2.5 py-1 rounded">
            {user.role === "admin" ? "Administrateur" : "Agent"}
          </div>
        </div>
      </div>
      <div className="inst-card p-6 space-y-3">
        <h2 className="font-semibold text-gray-900">Informations</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><div className="text-xs uppercase tracking-wider text-gray-500">Compte créé</div><div className="text-gray-800 mt-1">{formatDate(user.created_at)}</div></div>
          <div><div className="text-xs uppercase tracking-wider text-gray-500">Statut</div><div className="text-gray-800 mt-1">{user.is_active ? "Actif" : "Désactivé"}</div></div>
        </div>
      </div>
    </div>
  );
}
