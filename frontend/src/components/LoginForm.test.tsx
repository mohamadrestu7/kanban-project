import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AuthProvider } from "@/components/AuthProvider";
import { LoginForm } from "@/components/LoginForm";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace,
  }),
}));

const renderLogin = () =>
  render(
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  );

describe("LoginForm", () => {
  beforeEach(() => {
    window.localStorage.clear();
    replace.mockClear();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
        const rawBody = init?.body ? String(init.body) : "{}";
        const body = JSON.parse(rawBody) as { username?: string; password?: string };
        if (body.username === "user" && body.password === "password") {
          return new Response(
            JSON.stringify({ userId: "user_default", username: "user", token: "test-token" }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          );
        }
        return new Response(JSON.stringify({ detail: "Invalid credentials" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows an error for invalid credentials", async () => {
    renderLogin();

    await userEvent.type(screen.getByLabelText("Username"), "wrong");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      screen.getByText("Invalid username or password.")
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("stores the session and redirects for valid credentials", async () => {
    renderLogin();

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      const stored = window.localStorage.getItem("pm-auth-user");
      expect(stored).toBeTruthy();
      expect(JSON.parse(stored ?? "{}")).toMatchObject({
        userId: "user_default",
        username: "user",
      });
    });
    expect(replace).toHaveBeenCalledWith("/");
  });
});

