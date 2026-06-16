export type ApiLoginResponse = {
  userId: string;
  username: string;
  token: string;
};

export type ApiConversationMessage = {
  id: string;
  role: "user" | "assistant";
  message: string;
  created_at: string;
};

export type ApiAiBoardUpdateCard = {
  id?: string | null;
  action: string;
  title?: string | null;
  details?: string | null;
  columnId?: string | null;
  position?: number | null;
};

export type ApiAiBoardUpdateColumn = {
  id: string;
  title: string;
};

export type ApiAiChatResponse = {
  message: string;
  boardUpdates?: {
    cards: ApiAiBoardUpdateCard[];
    columns: ApiAiBoardUpdateColumn[];
  } | null;
};

export type ApiCardResponse = {
  id: string;
  title: string;
  details: string;
  columnId: string;
  position: number;
};

export type ApiBoardResponse = {
  id: string;
  title: string;
  userId: string;
  columns: Array<{
    id: string;
    title: string;
    position: number;
    cardIds: string[];
  }>;
  cards: Record<
    string,
    {
      id: string;
      title: string;
      details: string;
      columnId: string;
      position: number;
    }
  >;
};

const STORAGE_KEY = "pm-auth-user";

const getToken = (): string | null => {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { token?: string };
    return typeof parsed.token === "string" ? parsed.token : null;
  } catch {
    return null;
  }
};

const defaultBaseUrl = "http://127.0.0.1:8000";

export const apiBaseUrl = () =>
  (process.env.NEXT_PUBLIC_API_URL || defaultBaseUrl).replace(/\/$/, "");

class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

type RequestJsonInit = Omit<RequestInit, "body"> & { body?: unknown };

const requestJson = async <T>(
  path: string,
  init?: RequestJsonInit
): Promise<T> => {
  const url = `${apiBaseUrl()}${path.startsWith("/") ? "" : "/"}${path}`;
  const headers = new Headers(init?.headers as HeadersInit | undefined);
  headers.set("Accept", "application/json");
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body: BodyInit | null | undefined;
  if (init?.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(init.body);
  }

  const { body: _body, ...restInit } = init ?? {};
  const response = await fetch(url, {
    ...restInit,
    headers,
    body,
  });

  const text = await response.text();
  const parsed = text ? (JSON.parse(text) as unknown) : null;

  if (!response.ok) {
    throw new ApiError(`Request failed (${response.status})`, response.status, parsed);
  }

  return parsed as T;
};

export const api = {
  login: (username: string, password: string) =>
    requestJson<ApiLoginResponse>("/api/login", {
      method: "POST",
      body: { username, password },
    }),

  aiHistory: (userId: string, boardId: string) =>
    requestJson<ApiConversationMessage[]>(
      `/api/ai/history?user_id=${encodeURIComponent(userId)}&board_id=${encodeURIComponent(boardId)}`
    ),

  aiChat: (payload: { user_id: string; board_id?: string | null; message: string }) =>
    requestJson<ApiAiChatResponse>("/api/ai/chat", {
      method: "POST",
      body: payload,
    }),

  getBoard: (userIdOrUsername: string) =>
    requestJson<ApiBoardResponse>(`/api/users/${encodeURIComponent(userIdOrUsername)}/board`),

  renameColumn: (boardId: string, columnId: string, title: string) =>
    requestJson(`/api/boards/${encodeURIComponent(boardId)}/columns/${encodeURIComponent(columnId)}`, {
      method: "PUT",
      body: { title },
    }),

  createCard: (columnId: string, title: string, details: string) =>
    requestJson<ApiCardResponse>(`/api/columns/${encodeURIComponent(columnId)}/cards`, {
      method: "POST",
      body: { title, details },
    }),

  updateCard: (cardId: string, payload: { title?: string; details?: string }) =>
    requestJson(`/api/cards/${encodeURIComponent(cardId)}`, {
      method: "PUT",
      body: payload,
    }),

  deleteCard: (cardId: string) =>
    requestJson(`/api/cards/${encodeURIComponent(cardId)}`, { method: "DELETE" }),

  moveCard: (cardId: string, columnId: string, position: number) =>
    requestJson(`/api/cards/${encodeURIComponent(cardId)}/move`, {
      method: "PATCH",
      body: { column_id: columnId, position },
    }),
};

