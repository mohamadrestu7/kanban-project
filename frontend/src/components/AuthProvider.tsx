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

type AuthState = {
  isReady: boolean;
  isLoggedIn: boolean;
  username: string | null;
  login: (username: string, password: string) => boolean;
  logout: () => void;
};

const STORAGE_KEY = "pm-auth-user";
const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";
const AUTH_CHANGE_EVENT = "pm-auth-change";

const AuthContext = createContext<AuthState | null>(null);

const getStoredUsername = () => window.localStorage.getItem(STORAGE_KEY);
const getServerUsername = () => null;
const subscribeToAuth = (onStoreChange: () => void) => {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener(AUTH_CHANGE_EVENT, onStoreChange);

  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener(AUTH_CHANGE_EVENT, onStoreChange);
  };
};

const notifyAuthChanged = () => {
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isReady, setIsReady] = useState(false);
  const username = useSyncExternalStore(
    subscribeToAuth,
    getStoredUsername,
    getServerUsername
  );

  useEffect(() => {
    const readyTimer = window.setTimeout(() => setIsReady(true), 0);
    return () => window.clearTimeout(readyTimer);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      isReady,
      isLoggedIn: Boolean(username),
      username,
      login: (nextUsername, password) => {
        if (nextUsername !== VALID_USERNAME || password !== VALID_PASSWORD) {
          return false;
        }

        window.localStorage.setItem(STORAGE_KEY, nextUsername);
        notifyAuthChanged();
        return true;
      },
      logout: () => {
        window.localStorage.removeItem(STORAGE_KEY);
        notifyAuthChanged();
      },
    }),
    [isReady, username]
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
