import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "@/components/LoginForm";

describe("LoginForm", () => {
  it("renders username and password inputs", () => {
    render(<LoginForm onLogin={() => true} />);
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("submits form with user credentials", async () => {
    const onLogin = vi.fn().mockReturnValue(true);
    render(<LoginForm onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(onLogin).toHaveBeenCalledWith("user", "password");
  });

  it("displays error message on invalid credentials", async () => {
    const onLogin = vi.fn().mockReturnValue(false);
    render(<LoginForm onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "badpass");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid username or password/i);
  });
});
