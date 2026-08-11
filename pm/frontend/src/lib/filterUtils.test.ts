import { describe, expect, it } from "vitest";
import type { BoardData } from "./kanban";
import {
  defaultFilterOptions,
  defaultSortOption,
  extractAvailableTags,
  filterAndSortBoard,
  getActiveFilterCount,
  hasActiveFilters,
  type FilterOptions,
} from "./filterUtils";

describe("filterUtils", () => {
  const sampleBoard: BoardData = {
    columns: [
      { id: "col-1", title: "Backlog", cardIds: ["card-1", "card-2"] },
      { id: "col-2", title: "In Progress", cardIds: ["card-3"] },
    ],
    cards: {
      "card-1": {
        id: "card-1",
        title: "Build Search Bar",
        details: "Implement search by title and description.",
        priority: "high",
        dueDate: "2026-08-01", // Overdue relative to 2026-08-10
        tags: ["search", "frontend"],
        createdAt: "2026-08-01T10:00:00Z",
        updatedAt: "2026-08-05T10:00:00Z",
      },
      "card-2": {
        id: "card-2",
        title: "Setup SQLite DB",
        details: "Configure schema migrations.",
        priority: "low",
        dueDate: "2026-12-31",
        tags: ["backend", "db"],
        createdAt: "2026-08-02T10:00:00Z",
        updatedAt: "2026-08-02T10:00:00Z",
      },
      "card-3": {
        id: "card-3",
        title: "Design UX Mockup",
        details: "Create responsive dark theme layouts.",
        priority: "medium",
        dueDate: null,
        tags: ["design"],
        createdAt: "2026-08-03T10:00:00Z",
        updatedAt: "2026-08-08T10:00:00Z",
      },
    },
  };

  it("extracts unique sorted tags", () => {
    const tags = extractAvailableTags(sampleBoard.cards);
    expect(tags).toEqual(["backend", "db", "design", "frontend", "search"]);
  });

  it("returns full board when default filters and sort are applied", () => {
    const result = filterAndSortBoard(
      sampleBoard,
      defaultFilterOptions,
      defaultSortOption
    );
    expect(Object.keys(result.cards).length).toBe(3);
    expect(hasActiveFilters(defaultFilterOptions, defaultSortOption)).toBe(false);
    expect(getActiveFilterCount(defaultFilterOptions, defaultSortOption)).toBe(0);
  });

  it("filters by search query matching title and details", () => {
    const filters: FilterOptions = {
      ...defaultFilterOptions,
      searchQuery: "sqlite",
    };
    const result = filterAndSortBoard(sampleBoard, filters, "default");
    expect(Object.keys(result.cards)).toEqual(["card-2"]);
  });

  it("filters by priority", () => {
    const filters: FilterOptions = {
      ...defaultFilterOptions,
      priority: "high",
    };
    const result = filterAndSortBoard(sampleBoard, filters, "default");
    expect(Object.keys(result.cards)).toEqual(["card-1"]);
  });

  it("filters by column / status", () => {
    const filters: FilterOptions = {
      ...defaultFilterOptions,
      columnId: "col-2",
    };
    const result = filterAndSortBoard(sampleBoard, filters, "default");
    expect(result.columns[0].cardIds).toEqual([]);
    expect(result.columns[1].cardIds).toEqual(["card-3"]);
  });

  it("filters by tag", () => {
    const filters: FilterOptions = {
      ...defaultFilterOptions,
      tag: "frontend",
    };
    const result = filterAndSortBoard(sampleBoard, filters, "default");
    expect(Object.keys(result.cards)).toEqual(["card-1"]);
  });

  it("filters by due date (overdue vs no-due-date)", () => {
    const overdueFilters: FilterOptions = {
      ...defaultFilterOptions,
      dueDateFilter: "overdue",
    };
    const overdueResult = filterAndSortBoard(sampleBoard, overdueFilters, "default");
    expect(Object.keys(overdueResult.cards)).toEqual(["card-1"]);

    const noDueDateFilters: FilterOptions = {
      ...defaultFilterOptions,
      dueDateFilter: "no-due-date",
    };
    const noDueDateResult = filterAndSortBoard(sampleBoard, noDueDateFilters, "default");
    expect(Object.keys(noDueDateResult.cards)).toEqual(["card-3"]);
  });

  it("sorts cards by priority-desc and created-desc", () => {
    const priorityResult = filterAndSortBoard(
      sampleBoard,
      defaultFilterOptions,
      "priority-desc"
    );
    expect(priorityResult.columns[0].cardIds).toEqual(["card-1", "card-2"]);

    const createdResult = filterAndSortBoard(
      sampleBoard,
      defaultFilterOptions,
      "created-desc"
    );
    expect(createdResult.columns[0].cardIds).toEqual(["card-2", "card-1"]);
  });

  it("calculates active filter count and reset state", () => {
    const filters: FilterOptions = {
      searchQuery: "build",
      priority: "high",
      columnId: "all",
      tag: "search",
      dueDateFilter: "all",
    };
    expect(hasActiveFilters(filters, "title-asc")).toBe(true);
    expect(getActiveFilterCount(filters, "title-asc")).toBe(4);
  });
});
