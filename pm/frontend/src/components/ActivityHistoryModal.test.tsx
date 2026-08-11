import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ActivityHistoryModal } from "./ActivityHistoryModal";
import * as api from "@/lib/api";

describe("ActivityHistoryModal Component", () => {
  const sampleActivities: api.ActivityItem[] = [
    {
      id: "act-1",
      projectId: "proj-1",
      userId: "user",
      actionType: "card_created",
      entityType: "card",
      entityId: "card-10",
      message: "Created task 'Build Login Page'",
      createdAt: "2026-08-10T12:00:00Z",
    },
    {
      id: "act-2",
      projectId: "proj-1",
      userId: "user",
      actionType: "card_updated",
      entityType: "card",
      entityId: "card-10",
      message: "Updated task 'Build Login Page'",
      createdAt: "2026-08-10T12:05:00Z",
    },
  ];

  it("does not render when isOpen is false", () => {
    render(
      <ActivityHistoryModal
        isOpen={false}
        onClose={vi.fn()}
        projectId="proj-1"
        projectName="Main Project"
      />
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("fetches and displays activity log items when open", async () => {
    vi.spyOn(api, "fetchProjectActivity").mockResolvedValueOnce(sampleActivities);

    render(
      <ActivityHistoryModal
        isOpen={true}
        onClose={vi.fn()}
        projectId="proj-1"
        projectName="Main Project"
      />
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Activity History/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Created task 'Build Login Page'")).toBeInTheDocument();
      expect(screen.getByText("Updated task 'Build Login Page'")).toBeInTheDocument();
    });
  });
});
