import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/components/LoginForm";

describe("LoginForm", () => {
  it("renders username and password inputs", () => {
    render(<LoginForm onLogin={() => true} />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThan(0);
  });

  it("submits form with user credentials", async () => {
    const onLogin = vi.fn().mockReturnValue(true);
    const { container } = render(<LoginForm onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    const submitBtn = container.querySelector('button[type="submit"]')!;
    await userEvent.click(submitBtn);

    expect(onLogin).toHaveBeenCalledWith("user", "password");
  });

  it("displays error message on invalid credentials", async () => {
    const onLogin = vi.fn().mockReturnValue(false);
    const { container } = render(<LoginForm onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "badpass");
    const submitBtn = container.querySelector('button[type="submit"]')!;
    await userEvent.click(submitBtn);

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid username or password/i);
  });

  it("switches mode to Create Account on tab click", async () => {
    render(<LoginForm onLogin={() => true} />);
    const createTab = screen.getByRole("button", { name: "Create Account" });
    await userEvent.click(createTab);

    expect(screen.getByRole("heading", { name: "Register Account" })).toBeInTheDocument();
  });
});
