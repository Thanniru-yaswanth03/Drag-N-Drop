# Drag-N-Drop
# 🗂️ Drag N Drop Kanban Board

A modern Kanban-style project management application with drag-and-drop
functionality for organizing tasks across different workflow columns.

## 🚀 Live Demo

[View Live Demo](https://drag-n-drop-lilac.vercel.app/)

## 📸 Screenshots

### Kanban Board
![Kanban Board](./screenshots/board.png)

### Drag & Drop
![Drag and Drop](./screenshots/drag-drop.png)

---

## ✨ Features

- 🖱️ Drag and drop cards between columns
- ↕️ Reorder cards within a column
- ✏️ Create and edit tasks
- 🗑️ Delete tasks
- 📋 Create and manage Kanban columns
- 🔄 Move tasks between different workflow stages
- 💾 Persist board data using local storage
- 📱 Responsive UI
- ⚡ Fast client-side interactions

---

## 🛠️ Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Drag & Drop
- @dnd-kit/core
- @dnd-kit/sortable

### State & Persistence
- React Hooks
- Local Storage

### Development Tools
- Git
- GitHub
- VS Code

---

## 🏗️ Project Structure

```text
project/
├── app/
│   ├── page.tsx
│   └── ...
├── components/
│   ├── Board/
│   ├── Column/
│   ├── Card/
│   └── ...
├── hooks/
│   └── useBoard.ts
├── lib/
│   └── ...
├── public/
├── package.json
└── README.md
