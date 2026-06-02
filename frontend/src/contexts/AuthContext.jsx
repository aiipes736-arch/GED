import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from "react";
import api, { formatApiError } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = loading, false = not auth, obj = auth
  const [initialized, setInitialized] = useState(false);

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch (err) {
      // 401 is expected when not logged in; log other errors
      if (err.response?.status && err.response.status !== 401) {
        console.error("AuthContext.fetchMe failed:", err);
      }
      setUser(false);
    } finally {
      setInitialized(true);
    }
  }, []);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const login = useCallback(async (email, password) => {
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setUser(data);
      return { ok: true, user: data };
    } catch (e) {
      return { ok: false, error: formatApiError(e.response?.data?.detail) || e.message };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/auth/logout");
    } catch (err) {
      console.error("AuthContext.logout failed:", err);
    }
    setUser(false);
  }, []);

  const value = useMemo(
    () => ({ user, setUser, login, logout, initialized, refresh: fetchMe }),
    [user, login, logout, initialized, fetchMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
