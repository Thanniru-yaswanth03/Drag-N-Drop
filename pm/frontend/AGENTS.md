# Frontend Architecture & Implementation

## Overview

The `frontend` directory contains a single-page Next.js 16 (App Router) client application for a single-board Kanban studio.

## Technology Stack

- Framework: Next.js 16.1.6 (App Router)
- Library: React 19.2.3
- Styling: TailwindCSS v4 with CSS variables in globals.css
- Drag and Drop: `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- Unit Testing: Vitest 3.2.4 + `@testing-library/react` + `jsdom`
- End-to-End Testing: Playwright 1.58.0

## Directory Structure

```
frontend/
├── package.json
├── vitest.config.ts
├── playwright.config.ts
├── next.config.ts
├── postcss.config.mjs
├── tsconfig.json
├── tests/
│   └── kanban.spec.ts
└── src/
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   └── page.tsx
    ├── components/
    │   ├── KanbanBoard.tsx
    │   ├── KanbanBoard.test.tsx
    │   ├── KanbanColumn.tsx
    │   ├── KanbanCard.tsx
    │   ├── KanbanCardPreview.tsx
    │   └── NewCardForm.tsx
    └── lib/
        ├── kanban.ts
        └── kanban.test.ts
```

## Data Types and Board Logic (`src/lib/kanban.ts`)

- `Card`: `{ id: string; title: string; details: string; }`
- `Column`: `{ id: string; title: string; cardIds: string[]; }`
- `BoardData`: `{ columns: Column[]; cards: Record<string, Card>; }`
- `initialData`: Pre-populated board with 5 columns (Backlog, Discovery, In Progress, Review, Done) and 8 cards.
- `moveCard(columns, activeId, overId)`: Pure helper function to handle card reordering within a column or moving cards between columns.
- `createId(prefix)`: Generates unique alphanumeric string IDs.

## Component Hierarchy

- `page.tsx`: Entry page rendering `<KanbanBoard />`.
- `KanbanBoard`: Main container. Holds `board` state (`BoardData`) and `activeCardId` state. Manages `@dnd-kit` `DndContext`, `PointerSensor` activation constraints, drag overlays, column title edits, card additions, and card deletions.
- `KanbanColumn`: Column wrapper component. Implements `useDroppable` and `SortableContext`. Displays editable column title input, card count badge, card list, and card creation trigger.
- `KanbanCard`: Individual sortable card item. Implements `useSortable` for drag listeners and transforms. Displays title, details, and delete button.
- `KanbanCardPreview`: Floating ghost card preview rendered inside `DragOverlay` during drag operations.
- `NewCardForm`: Inline card creation form. Expands to accept title and details, then calls `onAdd`.

## Styling and Theme Tokens (`src/app/globals.css`)

The application follows the project design specification:
- Accent Yellow: `--accent-yellow: #ecad0a`
- Blue Primary: `--primary-blue: #209dd7`
- Purple Secondary: `--secondary-purple: #753991`
- Dark Navy: `--navy-dark: #032147`
- Gray Text: `--gray-text: #888888`
- Surface: `--surface: #f7f8fb`

## Test Coverage

- Unit Tests (`npm run test:unit`):
  - `src/lib/kanban.test.ts`: Verifies `moveCard` logic for reordering within columns, cross-column moves, and dropping onto empty columns.
  - `src/components/KanbanBoard.test.tsx`: Verifies board rendering (5 columns), column title updating, card addition, and card deletion.
- E2E Tests (`npm run test:e2e`):
  - `tests/kanban.spec.ts`: End-to-end tests validating board loads, card addition, and mouse drag-and-drop interactions.
