/**
 * Design System Tokens
 * Based on Linear/Apple hierarchy
 *
 * COLOR HIERARCHY:
 * - Base: Main background (lightest)
 * - Surface: Cards, panels (elevated)
 * - Overlay: Dialogs, dropdowns (highest)
 * - Border: Subtle dividers
 * - Interactive: Hover/Active states
 */

export const colors = {
  // Background layers (strict hierarchy)
  base: '#FAFAFA',        // Page background (zinc-50)
  surface: '#FFFFFF',     // Cards, panels (white)
  overlay: '#FFFFFF',     // Dialogs, menus (white + shadow)

  // Borders (subtle to prominent)
  border: {
    subtle: '#F4F4F5',    // zinc-100
    default: '#E4E4E7',   // zinc-200
    strong: '#D4D4D8',    // zinc-300
  },

  // Text (hierarchy)
  text: {
    primary: '#000000',   // Headings, important
    secondary: '#52525B', // zinc-600 - Body text
    tertiary: '#A1A1AA',  // zinc-400 - Muted
    disabled: '#D4D4D8',  // zinc-300
  },

  // Interactive states
  interactive: {
    hover: '#FAFAFA',     // zinc-50
    active: '#F4F4F5',    // zinc-100
    selected: '#F4F4F5',  // zinc-100
  },

  // Accent (black/grey only)
  accent: {
    primary: '#000000',
    secondary: '#18181B',  // zinc-900
    tertiary: '#3F3F46',   // zinc-700
  },
} as const;

export const elevation = {
  // Shadow tokens for depth
  low: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  medium: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
  high: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
} as const;

export const spacing = {
  // Consistent spacing scale
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
} as const;

/**
 * Usage example:
 *
 * className="bg-[var(--color-base)]"
 * or directly:
 * className="bg-[#FAFAFA]"
 */
