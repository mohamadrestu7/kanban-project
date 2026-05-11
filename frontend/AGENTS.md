# Frontend Architecture

## Overview

The frontend is a NextJS 16.1 application using React 19 with Tailwind CSS for styling and dnd-kit for drag-and-drop functionality. Currently this is a pure frontend demo with in-memory state management.

## Technology Stack

- **Framework**: Next.js 16.1.6 (App Router)
- **UI Library**: React 19.2.3
- **Styling**: Tailwind CSS 4
- **Drag & Drop**: dnd-kit (6.3.1) with sortable plugin
- **Testing**: Vitest 3.2.4 (unit), Playwright 1.58.0 (E2E)
- **Type Safety**: TypeScript 5
- **Linting**: ESLint 9

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Home page, renders KanbanBoard
│   │   ├── layout.tsx        # Root layout
│   │   └── globals.css       # Global styles with CSS variables
│   ├── components/
│   │   ├── KanbanBoard.tsx   # Main board component (with state mgmt)
│   │   ├── KanbanColumn.tsx  # Column component (droppable area)
│   │   ├── KanbanCard.tsx    # Individual card component
│   │   ├── KanbanCardPreview.tsx # Drag preview
│   │   ├── NewCardForm.tsx   # Card creation form
│   │   └── *.test.tsx        # Unit tests
│   └── lib/
│       ├── kanban.ts         # Kanban state logic and types
│       └── kanban.test.ts    # Logic unit tests
├── tests/
│   ├── kanban.spec.ts        # E2E tests (playwright)
│   ├── setup.ts              # Test setup config
│   └── vitest.d.ts           # Vitest type definitions
├── public/                    # Static assets
└── package.json              # Dependencies and scripts
```

## Key Components

### KanbanBoard (src/components/KanbanBoard.tsx)

- Main stateful component using `useState` for board data
- Manages drag-and-drop with `dnd-kit/core` context
- Handles card operations: add, delete, rename column
- Uses `useMemo` to optimize card lookup
- Client-side only component ("use client")

### KanbanColumn (src/components/KanbanColumn.tsx)

- Displays a single column with draggable cards
- Editable column title
- Card count display
- Uses `useDroppable` hook from dnd-kit
- Renders NewCardForm and KanbanCard children

### KanbanCard (src/components/KanbanCard.tsx)

- Individual task card
- Uses dnd-kit's `useSortable` hook
- Displays title and details
- Delete button functionality

### Data Types (src/lib/kanban.ts)

```typescript
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

### State Management

- **Location**: Client-side React hooks in KanbanBoard
- **Scope**: Single board, in-memory (no persistence)
- **Key functions**:
  - `moveCard()` - handles drag-and-drop logic
  - `createId()` - generates unique IDs
  - `initialData` - demo board seed data

## Styling Approach

- CSS variables for theming (defined in globals.css)
- Tailwind utility-first CSS
- Color scheme variables: `--accent-yellow`, `--blue-primary`, `--purple-secondary`, `--navy-dark`, `--gray-text`
- No component libraries (pure Tailwind)

## Test Coverage

- Unit tests for kanban logic and components (vitest)
- E2E tests for user flows (playwright)
- Tests verify: drag/drop, add/delete cards, rename columns

## Planned Changes for Integration

- Add authentication layer (login/logout)
- Connect to backend API instead of in-memory state
- Add sidebar for AI chat feature
- Persist data via API calls to FastAPI backend
