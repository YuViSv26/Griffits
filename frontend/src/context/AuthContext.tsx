import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  api,
  clearToken,
  setToken,
  type InitResponse,
  type LoginCodeAuthPayload,
} from "../api/client";

interface AuthContextValue {
  user: InitResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (payload: LoginCodeAuthPayload) => Promise<void>;
  register: (payload: LoginCodeAuthPayload) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<InitResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await api.init();
      setUser(data.authenticated ? data : null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, [refresh]);

  const login = useCallback(
    async (payload: LoginCodeAuthPayload) => {
      const res = await api.login(payload);
      setToken(res.access_token);
      await refresh();
    },
    [refresh]
  );

  const register = useCallback(
    async (payload: LoginCodeAuthPayload) => {
      const res = await api.register(payload);
      setToken(res.access_token);
      await refresh();
    },
    [refresh]
  );

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      clearToken();
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, refresh, login, register, logout }),
    [user, loading, refresh, login, register, logout]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
