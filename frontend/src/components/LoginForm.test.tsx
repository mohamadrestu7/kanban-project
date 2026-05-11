import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
  });

  it("shows an error for invalid credentials", async () => {
    renderLogin();

    await userEvent.type(screen.getByLabelText("Username"), "wrong");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      screen.getByText("Use username user and password password.")
    ).toBeInTheDocument();
    expect(replace).not.toHaveBeenCalled();
  });

  it("stores the session and redirects for valid credentials", async () => {
    renderLogin();

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(window.localStorage.getItem("pm-auth-user")).toBe("user");
    });
    expect(replace).toHaveBeenCalledWith("/");
  });
});

