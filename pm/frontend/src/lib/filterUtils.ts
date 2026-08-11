import type { BoardData, Card } from "@/lib/kanban";

export type PriorityFilterType = "all" | "high" | "medium" | "low";

export type DueDateFilterType =
  | "all"
  | "overdue"
  | "today"
  | "this-week"
  | "has-due-date"
  | "no-due-date";

export type SortOptionType =
  | "default"
  | "created-desc"
  | "created-asc"
  | "updated-desc"
  | "due-asc"
  | "due-desc"
  | "priority-desc"
  | "priority-asc"
  | "title-asc"
  | "title-desc";

export type FilterOptions = {
  searchQuery: string;
  priority: PriorityFilterType;
  columnId: string;
  tag: string;
  dueDateFilter: DueDateFilterType;
};

export const defaultFilterOptions: FilterOptions = {
  searchQuery: "",
  priority: "all",
  columnId: "all",
  tag: "all",
  dueDateFilter: "all",
};

export const defaultSortOption: SortOptionType = "default";

/**
 * Extracts all unique tags across the board cards.
 */
export function extractAvailableTags(cards: Record<string, Card>): string[] {
  const tagSet = new Set<string>();
  Object.values(cards).forEach((card) => {
    if (Array.isArray(card.tags)) {
      card.tags.forEach((tag) => {
        const trimmed = tag.trim();
        if (trimmed) {
          tagSet.add(trimmed);
        }
      });
    }
  });
  return Array.from(tagSet).sort((a, b) => a.localeCompare(b));
}

/**
 * Checks whether any filter or sort option is active.
 */
export function hasActiveFilters(
  filters: FilterOptions,
  sort: SortOptionType
): boolean {
  return (
    Boolean(filters.searchQuery.trim()) ||
    filters.priority !== "all" ||
    filters.columnId !== "all" ||
    filters.tag !== "all" ||
    filters.dueDateFilter !== "all" ||
    sort !== "default"
  );
}

/**
 * Counts how many filter criteria are currently active.
 */
export function getActiveFilterCount(
  filters: FilterOptions,
  sort: SortOptionType
): number {
  let count = 0;
  if (filters.searchQuery.trim()) count++;
  if (filters.priority !== "all") count++;
  if (filters.columnId !== "all") count++;
  if (filters.tag !== "all") count++;
  if (filters.dueDateFilter !== "all") count++;
  if (sort !== "default") count++;
  return count;
}

const PRIORITY_RANK: Record<string, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

function sortCardIds(
  cardIds: string[],
  cardsMap: Record<string, Card>,
  sort: SortOptionType
): string[] {
  if (sort === "default") {
    return cardIds;
  }

  const sorted = [...cardIds];
  sorted.sort((idA, idB) => {
    const cardA = cardsMap[idA];
    const cardB = cardsMap[idB];
    if (!cardA || !cardB) return 0;

    switch (sort) {
      case "created-desc": {
        const timeA = cardA.createdAt ? new Date(cardA.createdAt).getTime() : 0;
        const timeB = cardB.createdAt ? new Date(cardB.createdAt).getTime() : 0;
        return timeB - timeA;
      }
      case "created-asc": {
        const timeA = cardA.createdAt ? new Date(cardA.createdAt).getTime() : 0;
        const timeB = cardB.createdAt ? new Date(cardB.createdAt).getTime() : 0;
        return timeA - timeB;
      }
      case "updated-desc": {
        const timeA = cardA.updatedAt ? new Date(cardA.updatedAt).getTime() : 0;
        const timeB = cardB.updatedAt ? new Date(cardB.updatedAt).getTime() : 0;
        return timeB - timeA;
      }
      case "due-asc": {
        if (!cardA.dueDate) return 1;
        if (!cardB.dueDate) return -1;
        return new Date(cardA.dueDate).getTime() - new Date(cardB.dueDate).getTime();
      }
      case "due-desc": {
        if (!cardA.dueDate) return 1;
        if (!cardB.dueDate) return -1;
        return new Date(cardB.dueDate).getTime() - new Date(cardA.dueDate).getTime();
      }
      case "priority-desc": {
        const rankA = PRIORITY_RANK[cardA.priority || "medium"] || 2;
        const rankB = PRIORITY_RANK[cardB.priority || "medium"] || 2;
        return rankB - rankA;
      }
      case "priority-asc": {
        const rankA = PRIORITY_RANK[cardA.priority || "medium"] || 2;
        const rankB = PRIORITY_RANK[cardB.priority || "medium"] || 2;
        return rankA - rankB;
      }
      case "title-asc":
        return cardA.title.localeCompare(cardB.title);
      case "title-desc":
        return cardB.title.localeCompare(cardA.title);
      default:
        return 0;
    }
  });

  return sorted;
}

/**
 * Applies search, filters, and sorting to a BoardData object without mutating state.
 */
export function filterAndSortBoard(
  board: BoardData,
  filters: FilterOptions,
  sort: SortOptionType
): BoardData {
  const query = filters.searchQuery.toLowerCase().trim();
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);

  const weekLater = new Date(todayStart);
  weekLater.setDate(weekLater.getDate() + 7);

  const matchingCards: Record<string, Card> = {};

  for (const [id, card] of Object.entries(board.cards)) {
    // 1. Search Query Filter (title or details/description)
    if (query) {
      const matchTitle = card.title.toLowerCase().includes(query);
      const matchDetails = Boolean(
        card.details && card.details.toLowerCase().includes(query)
      );
      const matchDesc = Boolean(
        card.description && card.description.toLowerCase().includes(query)
      );
      if (!matchTitle && !matchDetails && !matchDesc) {
        continue;
      }
    }

    // 2. Priority Filter
    if (filters.priority !== "all") {
      const cardPriority = card.priority || "medium";
      if (cardPriority !== filters.priority) {
        continue;
      }
    }

    // 3. Tag Filter
    if (filters.tag !== "all") {
      const tags = Array.isArray(card.tags) ? card.tags : [];
      if (!tags.includes(filters.tag)) {
        continue;
      }
    }

    // 4. Due Date Filter
    if (filters.dueDateFilter !== "all") {
      const dueDateStr = card.dueDate;
      if (filters.dueDateFilter === "has-due-date" && !dueDateStr) {
        continue;
      }
      if (filters.dueDateFilter === "no-due-date" && dueDateStr) {
        continue;
      }

      if (
        filters.dueDateFilter === "overdue" ||
        filters.dueDateFilter === "today" ||
        filters.dueDateFilter === "this-week"
      ) {
        if (!dueDateStr) {
          continue;
        }
        const cardDate = new Date(dueDateStr);
        cardDate.setHours(0, 0, 0, 0);

        if (filters.dueDateFilter === "overdue" && cardDate >= todayStart) {
          continue;
        }
        if (
          filters.dueDateFilter === "today" &&
          cardDate.getTime() !== todayStart.getTime()
        ) {
          continue;
        }
        if (
          filters.dueDateFilter === "this-week" &&
          (cardDate < todayStart || cardDate > weekLater)
        ) {
          continue;
        }
      }
    }

    matchingCards[id] = card;
  }

  // Column filter & card ordering
  const filteredCols = board.columns.map((col) => {
    // 5. Column / Status Filter
    if (filters.columnId !== "all" && col.id !== filters.columnId) {
      return { ...col, cardIds: [] };
    }

    const colCardIds = col.cardIds.filter((id) => Boolean(matchingCards[id]));
    const sortedCardIds = sortCardIds(colCardIds, matchingCards, sort);

    return {
      ...col,
      cardIds: sortedCardIds,
    };
  });

  return {
    ...board,
    columns: filteredCols,
    cards: matchingCards,
  };
}
