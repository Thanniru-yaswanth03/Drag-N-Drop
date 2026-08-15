import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationCenterModal } from "./NotificationCenterModal";
import * as api from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    fetchNotificationsApi: vi.fn(),
    markNotificationReadApi: vi.fn(),
    markAllNotificationsReadApi: vi.fn(),
  };
});

describe("NotificationCenterModal Component", () => {
  const mockFetch = vi.mocked(api.fetchNotificationsApi);

  beforeEach(() => {
    mockFetch.mockResolvedValue({
      notifications: [
        {
          id: "n-1",
          type: "due_soon",
          title: "⏰ Task Due Soon: Test",
          message: "Task is due tomorrow",
          isRead: false,
        },
      ],
      unreadCount: 1,
    });
  });

  it("renders notifications when open", async () => {
    render(
      <NotificationCenterModal
        username="alice"
        isOpen={true}
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Task Due Soon: Test/i)).toBeInTheDocument();
    });
  });

  it("marks all notifications as read when clicking button", async () => {
    const mockMarkAll = vi.mocked(api.markAllNotificationsReadApi).mockResolvedValue(true);

    render(
      <NotificationCenterModal
        username="alice"
        isOpen={true}
        onClose={() => {}}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Mark all as read/i)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText(/Mark all as read/i));
    expect(mockMarkAll).toHaveBeenCalled();
  });
});
