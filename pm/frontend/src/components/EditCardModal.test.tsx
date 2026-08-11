import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EditCardModal } from "./EditCardModal";
import type { Card } from "@/lib/kanban";

describe("EditCardModal Component", () => {
  const sampleCard: Card = {
    id: "card-101",
    title: "Initial Task Title",
    details: "Initial task description",
    priority: "medium",
    dueDate: "2026-10-15",
    tags: ["feature", "ui"],
    assignee: "yash",
    createdAt: "2026-08-01T10:00:00Z",
    updatedAt: "2026-08-05T12:00:00Z",
  };

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <EditCardModal
        card={sampleCard}
        isOpen={false}
        onClose={vi.fn()}
        onSave={vi.fn()}
      />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders card fields when isOpen is true", () => {
    render(
      <EditCardModal
        card={sampleCard}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue("Initial Task Title")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Initial task description")).toBeInTheDocument();
    expect(screen.getByDisplayValue("2026-10-15")).toBeInTheDocument();
    expect(screen.getByDisplayValue("yash")).toBeInTheDocument();
    expect(screen.getByText("#feature")).toBeInTheDocument();
    expect(screen.getByText("#ui")).toBeInTheDocument();
  });

  it("adds and removes tags", () => {
    render(
      <EditCardModal
        card={sampleCard}
        isOpen={true}
        onClose={vi.fn()}
        onSave={vi.fn()}
      />
    );

    const tagInput = screen.getByPlaceholderText("New tag...");
    const addTagButton = screen.getByRole("button", { name: "+ Add Tag" });

    fireEvent.change(tagInput, { target: { value: "urgent" } });
    fireEvent.click(addTagButton);

    expect(screen.getByText("#urgent")).toBeInTheDocument();
  });

  it("submits updated card details on form submission", () => {
    const handleSave = vi.fn();
    const handleClose = vi.fn();

    render(
      <EditCardModal
        card={sampleCard}
        isOpen={true}
        onClose={handleClose}
        onSave={handleSave}
      />
    );

    const titleInput = screen.getByDisplayValue("Initial Task Title");
    fireEvent.change(titleInput, { target: { value: "Updated Title" } });

    const highPriorityButton = screen.getByRole("button", { name: "high" });
    fireEvent.click(highPriorityButton);

    const saveButton = screen.getByRole("button", { name: /save changes/i });
    fireEvent.click(saveButton);

    expect(handleSave).toHaveBeenCalledWith(
      "card-101",
      "Updated Title",
      "Initial task description",
      "high",
      "2026-10-15",
      ["feature", "ui"],
      "yash"
    );
    expect(handleClose).toHaveBeenCalled();
  });
});
