import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "../lib/api";

const SettingsContext = createContext({
  logo_url: "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/dmk2iip2_Photo%201.jpeg",
  hero_url: "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/15pprz55_Photo%202.jpeg",
  refresh: () => {},
});

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState({
    logo_url: "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/dmk2iip2_Photo%201.jpeg",
    hero_url: "https://customer-assets.emergentagent.com/job_ada3efd6-4e4c-4295-902b-4abf286154c2/artifacts/15pprz55_Photo%202.jpeg",
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/settings");
      const logo = data.logo_url?.startsWith("/api/") ? `${BACKEND_URL}${data.logo_url}` : data.logo_url;
      const hero = data.hero_url?.startsWith("/api/") ? `${BACKEND_URL}${data.hero_url}` : data.hero_url;
      setSettings({ logo_url: logo, hero_url: hero });
    } catch {
      // keep defaults
    }
  }, [BACKEND_URL]);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <SettingsContext.Provider value={{ ...settings, refresh }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  return useContext(SettingsContext);
}
