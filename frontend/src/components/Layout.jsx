import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { useAuth } from "../contexts/AuthContext";
import { Toaster } from "./ui/sonner";

export default function Layout() {
  const { user, initialized } = useAuth();
  if (!initialized) {
    return (
      <div className="flex items-center justify-center min-h-screen text-gray-500">Chargement...</div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="flex min-h-screen bg-[#f7f8f5]">
      <Sidebar />
      <main className="flex-1 min-w-0">
        <div className="px-6 sm:px-8 py-4 max-w-[1400px] mx-auto">
          <Header />
        </div>
        <div className="px-6 sm:px-8 pb-8 max-w-[1400px] mx-auto">
          <Outlet />
        </div>
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}
