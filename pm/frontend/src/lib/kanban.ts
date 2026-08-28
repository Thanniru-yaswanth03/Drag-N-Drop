export type Card = {
  id: string;
  title: string;
  details: string;
  description?: string;
  priority?: "high" | "medium" | "low";
  dueDate?: string | null;
  tags?: string[];
  assignee?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type Column = {
  id: string;
  title: string;
  cardIds: string[];
};

export type BoardData = {
  columns: Column[];
  cards: Record<string, Card>;
};

export const emptyBoardData: BoardData = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: [] },
    { id: "col-discovery", title: "Discovery", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
    { id: "col-review", title: "Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {},
};

export function sanitizeBoardData(boardData: BoardData): BoardData {
  if (!boardData || !boardData.columns || !Array.isArray(boardData.columns)) {
    return emptyBoardData;
  }
  const validCards: Record<string, Card> = {};
  const rawCards = boardData.cards || {};

  for (const [id, card] of Object.entries(rawCards)) {
    if (card && card.id && card.title) {
      validCards[id] = card;
    }
  }

  const seenCardIds = new Set<string>();
  const cleanColumns = boardData.columns.map((col) => {
    const cleanCardIds: string[] = [];
    const rawIds = Array.isArray(col.cardIds) ? col.cardIds : [];
    for (const cid of rawIds) {
      if (validCards[cid] && !seenCardIds.has(cid)) {
        seenCardIds.add(cid);
        cleanCardIds.push(cid);
      }
    }
    return {
      ...col,
      cardIds: cleanCardIds,
    };
  });

  return {
    ...boardData,
    columns: cleanColumns,
    cards: validCards,
  };
}

export const initialData: BoardData = {
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-init-1", "card-init-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-init-3", "card-init-4"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-init-5", "card-init-6"] },
    { id: "col-review", title: "Review", cardIds: ["card-init-7"] },
    { id: "col-done", title: "Done", cardIds: ["card-init-8", "card-init-9"] },
  ],
  cards: {
    "card-init-1": {
      id: "card-init-1",
      title: "Weekly team sprint planning & sync",
      details: "Review priorities, assign upcoming milestone deliverables, and update roadmap.",
      priority: "medium",
      dueDate: "2026-09-02",
      tags: ["Planning", "Team"],
      assignee: "yash",
    },
    "card-init-2": {
      id: "card-init-2",
      title: "Prepare monthly product metrics report",
      details: "Aggregate active user metrics, conversion funnels, and retention graphs for leadership review.",
      priority: "low",
      dueDate: "2026-09-05",
      tags: ["Analytics", "Report"],
      assignee: "alice",
    },
    "card-init-3": {
      id: "card-init-3",
      title: "Research customer feedback on mobile layout",
      details: "Analyze user suggestions regarding touch interactions, swipe gestures, and responsiveness.",
      priority: "medium",
      dueDate: "2026-09-03",
      tags: ["Research", "UX"],
      assignee: "user",
    },
    "card-init-4": {
      id: "card-init-4",
      title: "Evaluate transactional notification providers",
      details: "Benchmark deliverability, pricing tiers, and webhook latency across Resend and Postmark.",
      priority: "low",
      dueDate: "2026-09-08",
      tags: ["DevOps", "Email"],
      assignee: "bob",
    },
    "card-init-5": {
      id: "card-init-5",
      title: "Refactor navigation header & quick shortcuts",
      details: "Upgrade the Command Palette (Ctrl+K) and optimize keyboard navigation for fast task switching.",
      priority: "high",
      dueDate: "2026-08-30",
      tags: ["Frontend", "Feature"],
      assignee: "yash",
    },
    "card-init-6": {
      id: "card-init-6",
      title: "Optimize image assets and static bundling",
      details: "Convert static assets to WebP/AVIF format and enable caching headers on CDN edge nodes.",
      priority: "medium",
      dueDate: "2026-08-31",
      tags: ["Performance", "Web"],
      assignee: "bob",
    },
    "card-init-7": {
      id: "card-init-7",
      title: "Code Review: User profile & security settings",
      details: "Verify validation constraints, token expiry checks, and responsive mobile form layout.",
      priority: "high",
      dueDate: "2026-08-29",
      tags: ["Security", "Review"],
      assignee: "alice",
    },
    "card-init-8": {
      id: "card-init-8",
      title: "Launch Spatial Command Center design system",
      details: "Completed modern 3D visual redesign with obsidian theme, amber accents, and fast micro-interactions.",
      priority: "high",
      dueDate: "2026-08-28",
      tags: ["Design", "V1"],
      assignee: "yash",
    },
    "card-init-9": {
      id: "card-init-9",
      title: "Configure automated CI/CD pipeline and tests",
      details: "Configured full test suite verification and automatic deployment to production host.",
      priority: "medium",
      dueDate: "2026-08-27",
      tags: ["DevOps", "CI"],
      assignee: "bob",
    },
  },
};

const isColumnId = (columns: Column[], id: string) =>
  columns.some((column) => column.id === id);

const findColumnId = (columns: Column[], id: string) => {
  if (isColumnId(columns, id)) {
    return id;
  }
  return columns.find((column) => column.cardIds.includes(id))?.id;
};

export const moveCard = (
  columns: Column[],
  activeId: string,
  overId: string
): Column[] => {
  const activeColumnId = findColumnId(columns, activeId);
  const overColumnId = findColumnId(columns, overId);

  if (!activeColumnId || !overColumnId) {
    return columns;
  }

  const activeColumn = columns.find((column) => column.id === activeColumnId);
  const overColumn = columns.find((column) => column.id === overColumnId);

  if (!activeColumn || !overColumn) {
    return columns;
  }

  const isOverColumn = isColumnId(columns, overId);

  if (activeColumnId === overColumnId) {
    if (isOverColumn) {
      const nextCardIds = activeColumn.cardIds.filter(
        (cardId) => cardId !== activeId
      );
      nextCardIds.push(activeId);
      return columns.map((column) =>
        column.id === activeColumnId
          ? { ...column, cardIds: nextCardIds }
          : column
      );
    }

    const oldIndex = activeColumn.cardIds.indexOf(activeId);
    const newIndex = activeColumn.cardIds.indexOf(overId);

    if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) {
      return columns;
    }

    const nextCardIds = [...activeColumn.cardIds];
    nextCardIds.splice(oldIndex, 1);
    nextCardIds.splice(newIndex, 0, activeId);

    return columns.map((column) =>
      column.id === activeColumnId
        ? { ...column, cardIds: nextCardIds }
        : column
    );
  }

  const activeIndex = activeColumn.cardIds.indexOf(activeId);
  if (activeIndex === -1) {
    return columns;
  }

  const nextActiveCardIds = [...activeColumn.cardIds];
  nextActiveCardIds.splice(activeIndex, 1);

  const nextOverCardIds = [...overColumn.cardIds];
  if (isOverColumn) {
    nextOverCardIds.push(activeId);
  } else {
    const overIndex = overColumn.cardIds.indexOf(overId);
    const insertIndex = overIndex === -1 ? nextOverCardIds.length : overIndex;
    nextOverCardIds.splice(insertIndex, 0, activeId);
  }

  return columns.map((column) => {
    if (column.id === activeColumnId) {
      return { ...column, cardIds: nextActiveCardIds };
    }
    if (column.id === overColumnId) {
      return { ...column, cardIds: nextOverCardIds };
    }
    return column;
  });
};

export const createId = (prefix: string) => {
  const randomPart = Math.random().toString(36).slice(2, 8);
  const timePart = Date.now().toString(36);
  return `${prefix}-${randomPart}${timePart}`;
};
