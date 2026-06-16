"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { api } from "@/lib/api";

type AuthState = {
  isReady: boolean;
  isLoggedIn: boolean;
  username: string | null;
  userId: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
};

const STORAGE_KEY = "pm-auth-user";
const AUTH_CHANGE_EVENT = "pm-auth-change";

const AuthContext = createContext<AuthState | null>(null);

type StoredAuth = { userId: string; username: string; token: string };

const parseStoredAuth = (raw: string | null): StoredAuth | null => {
  if (!raw) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed &&
      typeof parsed === "object" &&
      "userId" in parsed &&
      "username" in parsed &&
      "token" in parsed &&
      typeof (parsed as StoredAuth).userId === "string" &&
      typeof (parsed as StoredAuth).username === "string" &&
      typeof (parsed as StoredAuth).token === "string"
    ) {
      return parsed as StoredAuth;
    }
  } catch {
    // ignore
  }
  return null;
};

const getStoredAuthSnapshot = () => {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
};
const getServerUsername = () => null;
const subscribeToAuth = (onStoreChange: () => void) => {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(AUTH_CHANGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(AUTH_CHANGE_EVENT, onStoreChange);
  };
};

const notifyAuthChanged = () => {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isReady, setIsReady] = useState(false);
  const storedSnapshot = useSyncExternalStore(
    subscribeToAuth,
    getStoredAuthSnapshot,
    getServerUsername
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const readyTimer = window.setTimeout(() => setIsReady(true), 0);
    return () => window.clearTimeout(readyTimer);
  }, []);

  const stored = useMemo(() => parseStoredAuth(storedSnapshot), [storedSnapshot]);
  const username = stored?.username ?? null;
  const userId = stored?.userId ?? null;

  const value = useMemo<AuthState>(
    () => ({
      isReady,
      isLoggedIn: Boolean(username),
      username,
      userId,
      login: async (nextUsername, password) => {
        try {
          const result = await api.login(nextUsername, password);
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
          notifyAuthChanged();
          return true;
        } catch {
          return false;
        }
      },
      logout: () => {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem(STORAGE_KEY);
        }
        notifyAuthChanged();
      },
    }),
    [isReady, userId, username]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
};
