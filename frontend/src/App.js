import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { SettingsProvider } from "./contexts/SettingsContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Documents from "./pages/Documents";
import Folders from "./pages/Folders";
import Agents from "./pages/Agents";
import Activity from "./pages/Activity";
import Reports from "./pages/Reports";
import Messages from "./pages/Messages";
import Inbox from "./pages/Inbox";
import Announcements from "./pages/Announcements";
import SettingsPage from "./pages/Settings";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <SettingsProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/folders" element={<Folders />} />
              <Route path="/archive" element={<Documents archivedView={true} />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/activity" element={<Activity />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/messages" element={<Messages />} />
              <Route path="/inbox" element={<Inbox />} />
              <Route path="/announcements" element={<Announcements />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </SettingsProvider>
  );
}
