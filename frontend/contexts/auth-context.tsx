"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { authAPI } from "@/lib/api";

export interface User {
  user_id: string;
  email: string;
  role: "owner" | "staff";
  tenant_ids: string[];
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password?: string, magicToken?: string) => Promise<void>;
  logout: () => Promise<void>;
  refetch: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const data = await authAPI.me();
      // Backend returns user data directly
      setUser({
        user_id: data.user_id,
        email: data.email,
        role: data.role,
        tenant_ids: data.tenants || []
      });
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const login = async (email: string, password?: string, magicToken?: string) => {
    await authAPI.login(email, password, magicToken);
    // After login, fetch full user info from /me endpoint (includes tenants)
    await fetchUser();
  };

  const logout = async () => {
    await authAPI.logout();
    setUser(null);
  };

  const refetch = async () => {
    setLoading(true);
    await fetchUser();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

