# AGI Time Blocking - Development Guidelines
*Adapted from Figma Make for our black/grey/white design system*

## Design System Constraints

**STRICT COLOR PALETTE - NO EXCEPTIONS:**
- Use ONLY semantic tokens from `styles/globals.css`
- Never hardcode colors (no `#000000`, `#ffffff`, etc.)
- Never use blue, green, red, or any colored utilities
- Only grayscale: black, white, zinc variants

**Available Semantic Tokens:**
```css
bg-background       /* Page base - #ffffff */
bg-card             /* Elevated panels - #ffffff */
bg-muted            /* Subtle backgrounds - #f4f4f5 */
bg-accent           /* Interactive hover - #f4f4f5 */
border-border       /* Dividers - #e4e4e7 */
text-foreground     /* Primary text - #000000 */
text-muted-foreground /* Secondary text - #71717a */
bg-primary          /* Black - #000000 */
text-primary-foreground /* White on black - #ffffff */
```

## Tailwind Guidance

**FORBIDDEN Classes:**
- ❌ Font utilities: `text-2xl`, `font-bold`, `leading-none` (unless explicitly requested)
- ❌ Colored backgrounds: `bg-blue-500`, `bg-green-600`, `bg-red-400`
- ❌ Colored text: `text-blue-600`, `text-green-500`, `text-red-700`
- ❌ Colored borders: `border-blue-500`, `border-green-600`
- ❌ Hardcoded colors in className or style attributes

**Required Typography:**
- Use default typography from `styles/globals.css` - NEVER override
- Each HTML element has pre-configured font-size, weight, line-height:
  - `<h1>` = text-2xl + font-medium
  - `<h2>` = text-xl + font-medium
  - `<h3>` = text-lg + font-medium
  - `<p>` = text-base + font-normal
  - `<button>` = text-base + font-medium
  - `<label>` = text-base + font-medium
- **CRITICAL**: Using Tailwind utilities like `text-sm`, `font-bold` will OVERRIDE globals.css and break consistency
- Only use HTML elements directly - NO font/size classes unless explicitly requested

## Component Guidelines

**React Components:**
- Create modular components in `/components` directory
- Import with: `import { ComponentName } from "./components/component-name.tsx"`
- Always provide unique `key` prop for list elements
- Use TypeScript `.tsx` files only

**ShadCN Components:**
- Import from: `import { ComponentName } from "./components/ui/component-name"`
- DO NOT create custom versions of ShadCN components
- Modify existing components minimally if needed
- Components available:
  - Layout: `card`, `separator`, `scroll-area`, `resizable`
  - Navigation: `tabs`, `breadcrumb`, `pagination`
  - Forms: `input`, `label`, `button`, `select`, `slider`, `checkbox`, `switch`
  - Overlays: `dialog`, `sheet`, `popover`, `dropdown-menu`, `tooltip`
  - Feedback: `alert`, `badge`, `skeleton`, `progress`
  - Data: `table`, `accordion`, `collapsible`

**Protected UI Directory:**
- `/components/ui` is ONLY for ShadCN components
- DO NOT create new files in `/components/ui`
- DO NOT overwrite existing ShadCN components

## Library Usage

**Required Imports:**
```tsx
import { Icon } from 'lucide-react';           // Icons (black only)
import { motion } from 'motion/react';          // Animations
import { toast } from "sonner@2.0.3";          // Toast notifications
import { useForm } from 'react-hook-form@7.55.0'; // Forms
```

**Recommended Libraries:**
- Charts: `recharts`
- Drag & Drop: `@dnd-kit/core` (already in project)
- Date: native `Date` API (no external libs)

**Forbidden Libraries:**
- ❌ Framer Motion (use Motion instead)
- ❌ react-resizable (use re-resizable)
- ❌ konva (use canvas directly)

## File Structure Rules

**Protected Files (DO NOT MODIFY):**
- `/components/figma/ImageWithFallback.tsx`
- `/styles/globals.css` (unless changing design tokens)
- All files in `/components/ui/` (ShadCN components)

**Main Entry Point:**
- Use `/App.tsx` as main component
- Must have default export
- Prefer multiple components over single monolithic file

## Images & Assets

**Image Handling:**
- Use `ImageWithFallback` component for new images
- Import: `import { ImageWithFallback } from './components/figma/ImageWithFallback'`
- Never use `<img>` tag directly
- For icons: use `lucide-react` (black color only)

## Code Quality

**Development Practices:**
- No placeholders (`// Rest of code`, `{/* Add elements */}`)
- Always include full implementation
- Use `edit_tool` for localized changes (<30% of file)
- Recreate files instead of editing newly created ones
- Mock external API responses with placeholder data

**Type Safety:**
- Use TypeScript strictly
- Define interfaces for props
- Avoid `any` type

## Design System Architecture

**Visual Hierarchy (from base to overlay):**
1. **Base Layer**: `bg-muted` (#f4f4f5) - Page background
2. **Surface Layer**: `bg-card` (#ffffff) - Panels, cards
3. **Interactive States**: `bg-accent` (#f4f4f5) - Hover effects
4. **Borders**: `border-border` (#e4e4e7) - Dividers
5. **Text Hierarchy**:
   - Primary: `text-foreground` (#000000)
   - Secondary: `text-muted-foreground` (#71717a)
   - Disabled: `text-muted-foreground/50`

**Spacing Scale (consistent):**
```tsx
gap-1   /* 4px */
gap-2   /* 8px */
gap-3   /* 12px */
gap-4   /* 16px */
gap-6   /* 24px */
gap-8   /* 32px */
```

## Output Format

1. **Start**: Briefly describe approach (1-2 sentences)
2. **Work**: Use internal thinking for complex logic
3. **Complete**: ONE paragraph summarizing what was implemented
4. **Optional**: 2-3 bullet point suggestions for next steps

**Example:**
> I'll create a time-blocking container component using our semantic tokens.
>
> *(work happens)*
>
> Created a modular container component with sidebar navigation, using bg-card for elevated panels and bg-muted for the base. All interactions use our black/grey/white palette with proper hover states via bg-accent.

## Common Mistakes to Avoid

❌ **DON'T:**
- Use `className="bg-white"` → Use `className="bg-card"`
- Use `className="bg-zinc-100"` → Use `className="bg-muted"`
- Use `className="text-gray-600"` → Use `className="text-muted-foreground"`
- Use `className="border-gray-200"` → Use `className="border-border"`
- Add font classes like `text-xl font-bold` → Use default typography
- Create colored badges/alerts → Use grayscale variants only
- Hardcode hex colors anywhere

✅ **DO:**
- Always use semantic tokens
- Preserve visual hierarchy
- Follow existing component patterns
- Keep it minimal and focused
- Test contrast for accessibility

---

*These guidelines ensure consistency with our strict black/grey/white design system while maintaining code quality and avoiding visual bugs.*
