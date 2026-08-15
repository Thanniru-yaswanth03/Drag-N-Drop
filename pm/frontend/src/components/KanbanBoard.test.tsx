import { render, screen, within, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

describe("KanbanBoard", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("pm_auth_token", "sess-test-token-12345");
    global.fetch = vi.fn().mockImplementation((url, options) => {
      const urlStr = typeof url === "string" ? url : url.toString();

      if (urlStr.includes("/api/auth/me")) {
        const token = localStorage.getItem("pm_auth_token");
        if (token) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ authenticated: true, user: "user" }),
          } as Response);
        }
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ detail: "Unauthorized" }),
        } as Response);
      }

      if (urlStr.includes("/api/projects")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [{ id: "board-1", name: "Main Project" }],
        } as Response);
      }

      if (urlStr.includes("/api/board")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            columns: [
              { id: "col-backlog", title: "Backlog", cardIds: [] },
              { id: "col-discovery", title: "Discovery", cardIds: [] },
              { id: "col-progress", title: "In Progress", cardIds: [] },
              { id: "col-review", title: "Review", cardIds: [] },
              { id: "col-done", title: "Done", cardIds: [] },
            ],
            cards: {},
          }),
        } as Response);
      }

      if (urlStr.includes("/api/cards") && options?.method === "POST") {
        const body = options?.body ? JSON.parse(options.body) : {};
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            success: true,
            card: {
              id: body.cardId || "card-test-1",
              title: body.title || "New card",
              details: body.details || "",
              description: body.details || "",
              priority: body.priority || "medium",
              columnId: body.columnId,
            },
          }),
        } as Response);
      }

      if (urlStr.includes("/api/cards") && options?.method === "DELETE") {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ success: true }),
        } as Response);
      }

      if (urlStr.includes("/api/auth/logout")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ success: true }),
        } as Response);
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      } as Response);
    });
  });

  it("renders login form when unauthenticated", async () => {
    localStorage.clear();
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThan(0);
    });
  });

  it("renders five columns when authenticated", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getByText(/Workspace by YASH/i)).toBeInTheDocument();
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });

    // Wait for initial board fetch to complete
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/board/),
        expect.any(Object)
      );
    });

    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    fireEvent.change(input, { target: { value: "New Name" } });
    await waitFor(() => {
      expect(input).toHaveValue("New Name");
    });
  });

  it("adds and removes a card", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getByText(/Main Project/i)).toBeInTheDocument();
      expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
    });
    const column = getFirstColumn();
    const openAddBtn = within(column).getByText(/Add Task/i);
    fireEvent.click(openAddBtn);

    const titleInput = await within(column).findByPlaceholderText(/Card title/i);
    fireEvent.change(titleInput, { target: { value: "New card" } });
    const detailsInput = within(column).getByPlaceholderText(/Details and context/i);
    fireEvent.change(detailsInput, { target: { value: "Notes" } });

    const form = titleInput.closest("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(within(column).getByText("New card")).toBeInTheDocument();
    });

    const deleteBtn = within(column).getByLabelText(/Delete New card/i);
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(within(column).queryByText("New card")).not.toBeInTheDocument();
    });
  });

  it("logs out user when clicking logout", async () => {
    render(<KanbanBoard />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
    });
    const logoutButton = screen.getByRole("button", { name: /logout/i });
    await userEvent.click(logoutButton);
    await waitFor(() => {
      expect(screen.getAllByRole("button", { name: /sign in/i }).length).toBeGreaterThan(0);
    });
  });
});
