/**
 * Solar Operations OS — Auth Context
 *
 * Provides: login, logout, currentUser, isAuthenticated, isLoading.
 * Listens for the global solar-os:unauthorized event to auto-logout.
 */
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import {
  authApi,
  clearSession,
  getSession,
  setSession,
} from '../lib/api';
import type { LoginRequest } from '../lib/api';

// ── Types ──────────────────────────────────────────────────────────────────────
export interface CurrentUser {
  sessionId: string;
  /** Organization slug shown in the header */
  orgSlug: string;
  email: string;
}

interface AuthState {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (creds: LoginRequest) => Promise<{ requiresTotp: boolean }>;
  logout: () => Promise<void>;
  verifyTotp: (code: string) => Promise<void>;
  loginAsDemo: () => void;
}

// ── Context ────────────────────────────────────────────────────────────────────
const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}

// ── Provider ───────────────────────────────────────────────────────────────────
interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const session = getSession();
    if (session && session.expiresAt > Date.now()) {
      // Token still valid — restore the user context
      // In a full implementation we'd decode the JWT; for now we store extra fields
      const stored = localStorage.getItem('solar_os_user');
      if (stored) {
        try {
          setUser(JSON.parse(stored) as CurrentUser);
        } catch {
          clearSession();
        }
      }
    } else {
      clearSession();
    }
    setIsLoading(false);
  }, []);

  // Listen for silent-refresh failure
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      clearSession();
      localStorage.removeItem('solar_os_user');
    };
    window.addEventListener('solar-os:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('solar-os:unauthorized', handleUnauthorized);
  }, []);

  const login = useCallback(async (creds: LoginRequest): Promise<{ requiresTotp: boolean }> => {
    const data = await authApi.login(creds);
    setSession({
      accessToken: data.access_token,
      sessionId: data.session_id,
      expiresAt: Date.now() + data.expires_in * 1000,
    });
    if (!data.requires_totp) {
      const currentUser: CurrentUser = {
        sessionId: data.session_id,
        orgSlug: creds.organization_slug,
        email: creds.email,
      };
      setUser(currentUser);
      localStorage.setItem('solar_os_user', JSON.stringify(currentUser));
    }
    return { requiresTotp: data.requires_totp };
  }, []);

  const verifyTotp = useCallback(async (code: string): Promise<void> => {
    const data = await authApi.verifyTotp(code);
    setSession({
      accessToken: data.access_token,
      sessionId: data.session_id,
      expiresAt: Date.now() + data.expires_in * 1000,
    });
    const stored = localStorage.getItem('solar_os_user');
    if (stored) {
      const u = JSON.parse(stored) as CurrentUser;
      setUser(u);
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await authApi.logout();
    } catch {
      // ignore — clear locally regardless
    }
    setUser(null);
    clearSession();
    localStorage.removeItem('solar_os_user');
  }, []);

  const loginAsDemo = useCallback((): void => {
    const demoUser: CurrentUser = {
      sessionId: 'demo-session-' + Date.now(),
      orgSlug: 'tata-power-solar',
      email: 'lead.architect@tatapower.com',
    };
    setUser(demoUser);
    localStorage.setItem('solar_os_user', JSON.stringify(demoUser));
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
        verifyTotp,
        loginAsDemo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
