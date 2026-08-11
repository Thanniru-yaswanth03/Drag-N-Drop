import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TaskFilterToolbar } from "./TaskFilterToolbar";
import { defaultFilterOptions, defaultSortOption } from "@/lib/filterUtils";

describe("TaskFilterToolbar Component", () => {
  const sampleColumns = [
    { id: "col-backlog", title: "Backlog", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
  ];
  const sampleTags = ["backend", "frontend", "ui"];

  it("renders search input, dropdowns, and sort options", () => {
    render(
      <TaskFilterToolbar
        columns={sampleColumns}
        availableTags={sampleTags}
        filters={defaultFilterOptions}
        sort={defaultSortOption}
        activeCount={0}
        onFilterChange={vi.fn()}
        onSortChange={vi.fn()}
        onReset={vi.fn()}
      />
    );

    expect(
      screen.getByPlaceholderText("Search tasks by title or description...")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by column status")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by priority")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by tag")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter by due date")).toBeInTheDocument();
    expect(screen.getByLabelText("Sort tasks by")).toBeInTheDocument();
  });

  it("triggers onFilterChange when typing search query", () => {
    const handleFilterChange = vi.fn();
    render(
      <TaskFilterToolbar
        columns={sampleColumns}
        availableTags={sampleTags}
        filters={defaultFilterOptions}
        sort={defaultSortOption}
        activeCount={0}
        onFilterChange={handleFilterChange}
        onSortChange={vi.fn()}
        onReset={vi.fn()}
      />
    );

    const input = screen.getByPlaceholderText("Search tasks by title or description...");
    fireEvent.change(input, { target: { value: "roadmap" } });

    expect(handleFilterChange).toHaveBeenCalledWith({
      ...defaultFilterOptions,
      searchQuery: "roadmap",
    });
  });

  it("renders clear filters button when activeCount > 0 and calls onReset", () => {
    const handleReset = vi.fn();
    render(
      <TaskFilterToolbar
        columns={sampleColumns}
        availableTags={sampleTags}
        filters={{ ...defaultFilterOptions, priority: "high" }}
        sort="priority-desc"
        activeCount={2}
        onFilterChange={vi.fn()}
        onSortChange={vi.fn()}
        onReset={handleReset}
      />
    );

    const clearButton = screen.getByRole("button", { name: /clear filters/i });
    expect(clearButton).toBeInTheDocument();

    fireEvent.click(clearButton);
    expect(handleReset).toHaveBeenCalledTimes(1);
  });
});
