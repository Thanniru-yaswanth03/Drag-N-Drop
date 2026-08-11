import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProjectMembersModal } from "./ProjectMembersModal";
import * as api from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchProjectMembers: vi.fn(),
    addProjectMemberApi: vi.fn(),
    removeProjectMemberApi: vi.fn(),
  };
});

describe("ProjectMembersModal Component", () => {
  const mockFetch = vi.mocked(api.fetchProjectMembers);

  beforeEach(() => {
    mockFetch.mockResolvedValue({
      members: [
        { id: "u-1", username: "alice", role: "owner" },
        { id: "u-2", username: "bob", role: "member" },
      ],
      userRole: "owner",
    });
  });

  it("renders member list when open", async () => {
    render(
      <ProjectMembersModal
        projectId="board-user"
        currentUsername="alice"
        isOpen={true}
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/@alice/i)).toBeInTheDocument();
      expect(screen.getByText(/@bob/i)).toBeInTheDocument();
    });
  });

  it("submits new member invitation", async () => {
    const mockAdd = vi.mocked(api.addProjectMemberApi).mockResolvedValue({
      success: true,
      member: { username: "charlie", role: "member" },
    });

    render(
      <ProjectMembersModal
        projectId="board-user"
        currentUsername="alice"
        isOpen={true}
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Username/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByPlaceholderText(/Username/i), "charlie");
    await userEvent.click(screen.getByRole("button", { name: /\+ Invite/i }));

    expect(mockAdd).toHaveBeenCalledWith("board-user", "charlie", "member", "alice");
  });
});
