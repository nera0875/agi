# AGI Time Blocking Dashboard

A strict time-blocking application designed for focus and productivity. Built with React + Vite + Tailwind CSS.

## Features

- **Container System**: Create time containers with hard limits (e.g., 60min max)
- **Block Management**: Divide containers into focused work blocks
- **Integrated Timers**: Each block has its own timer (Start/Pause/Reset)
- **Timeline Schedule**: Visual daily schedule (6h-24h) without scrolling
- **Task Tracking**: Add and check off tasks within blocks
- **localStorage Persistence**: All data saved locally - **works offline**

## Design Philosophy

- **Black/Grey/White Only**: Minimalist color palette for focus
- **Hard Limits**: Containers enforce strict time boundaries
- **No Infinite Scroll**: Compact timeline fits entire day on screen
- **Asperger-Friendly**: Clear structure, strict boundaries, no ambiguity

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

Visit `http://localhost:3000`

## Usage

### 1. Container Library

- Click **"New"** to create a container
- Set **Total Duration** (hard limit, cannot exceed)
- Set **Pause After** (auto-break when done)
- Add blocks inside container (click to enter)

### 2. Blocks

- Each block has a **name**, **duration**, and **color**
- Click **"Add Block"** inside a container
- Total block time cannot exceed container limit
- **Double-click** block name to edit inline

### 3. Timers

- Each block has integrated timer: **Start / Pause / Reset**
- Container timer enforces hard limit
- Auto-advances to next block when done
- Force stops at container limit

### 4. Today's Schedule

- Click **"Add"** to schedule a container
- Select time slot (15min intervals)
- Visual timeline shows entire day
- Hover to **Start** or **Delete** scheduled containers

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** for fast builds
- **Tailwind CSS v4** for styling
- **Radix UI** + **Shadcn** components
- **Lucide** icons (black only)
- **@dnd-kit** for drag & drop

## Offline First

All data is stored in `localStorage` - **no backend required**. The app works completely offline.

## Color Palette

```
Black:   #000000
Grey:    #71717a, #a1a1aa, #d4d4d8, #e4e4e7, #f4f4f5
White:   #ffffff
```

**NO blue, green, red, or other colors.**

## Development

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## License

MIT

---

🤖 Built with focus and discipline
