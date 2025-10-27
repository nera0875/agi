---
name: react-conventions
description: Figma Make architecture + ShadCN/UI + tokens sémantiques - système design noir/gris/blanc strict AGI
type: documentation
---

# FIGMA MAKE FRONTEND CONVENTIONS - AGI

*Convention complète développement frontend Figma Make avec React 18 + Tailwind + ShadCN/UI*

## 1. Architecture Figma Make

Système de construction applications web 0→1 basé sur React et Tailwind CSS. Approche **composant-first** pour créer prototypes, maquettes et applications fonctionnelles.

### 1.1 Objectifs
- Définir règles strictes développement frontend
- Éviter duplications et incohérences
- Maintenir structure Figma Make
- Assurer cohérence système design AGI

## 2. Système de Couleurs STRICT

### 2.1 Palette Autorisée (UNIQUEMENT tokens sémantiques)

```css
/* Tokens sémantiques - styles/globals.css */

/* Backgrounds */
bg-background           /* Page base - #ffffff */
bg-card                 /* Panneaux élevés - #ffffff */
bg-muted                /* Arrière-plans subtils - #f4f4f5 */
bg-accent               /* États interactifs hover - #f4f4f5 */
bg-primary              /* Noir - #000000 */
bg-secondary            /* Gris moyen - #f4f4f5 */

/* Bordures */
border-border           /* Diviseurs - #e4e4e7 */
border-input            /* Champs de saisie - #e4e4e7 */

/* Texte */
text-foreground         /* Texte principal - #000000 */
text-muted-foreground   /* Texte secondaire - #71717a */
text-primary-foreground /* Blanc sur noir - #ffffff */
text-secondary-foreground /* Noir sur gris - #000000 */

/* États */
bg-destructive          /* Erreurs - #000000 (pas de rouge) */
text-destructive-foreground /* #ffffff */
```

### 2.2 Hiérarchie Visuelle (base → overlays)

1. **Couche base** : `bg-muted` (#f4f4f5) - Arrière-plan page
2. **Couche surface** : `bg-card` (#ffffff) - Panneaux, cartes
3. **États interactifs** : `bg-accent` (#f4f4f5) - Hover
4. **Bordures** : `border-border` (#e4e4e7) - Diviseurs
5. **Hiérarchie texte** :
   - Principal : `text-foreground` (#000000)
   - Secondaire : `text-muted-foreground` (#71717a)
   - Désactivé : `text-muted-foreground/50`

### 2.3 Classes INTERDITES

```css
/* ❌ INTERDIT - Classes hardcodées */
bg-white, bg-black, bg-gray-100, bg-zinc-200
text-gray-600, text-slate-500, text-neutral-400
border-gray-200, border-slate-300

/* ❌ INTERDIT - Couleurs non-grayscale */
bg-blue-500, bg-green-600, bg-red-400
text-blue-600, text-green-500, text-red-700
border-blue-500, border-green-600

/* ❌ INTERDIT - Couleurs hexadécimales */
style={{ backgroundColor: '#ffffff' }}
style={{ color: '#000000' }}
```

## 3. ShadCN/UI Composants (47 disponibles)

### 3.1 Layout & Structure

```tsx
import { AspectRatio } from "@/components/ui/aspect-ratio"
// Affiche contenu dans ratio désiré

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
// Carte avec en-tête, contenu, pied

import { Separator } from "@/components/ui/separator"
// Sépare visuellement contenu

import { ScrollArea } from "@/components/ui/scroll-area"
// Scroll personnalisé

import { Resizable, ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
// Panneaux redimensionnables

import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
// Barre latérale composable
```

### 3.2 Navigation

```tsx
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb"
// Fil d'Ariane

import { NavigationMenu, NavigationMenuContent, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger } from "@/components/ui/navigation-menu"
// Menu navigation

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
// Onglets

import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination"
// Pagination
```

### 3.3 Forms & Inputs

```tsx
import { Button } from "@/components/ui/button"
// Bouton personnalisable

import { Input } from "@/components/ui/input"
// Champ texte

import { Textarea } from "@/components/ui/textarea"
// Zone texte multiligne

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
// Liste déroulante

import { Checkbox } from "@/components/ui/checkbox"
// Case à cocher

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
// Boutons radio

import { Switch } from "@/components/ui/switch"
// Interrupteur

import { Slider } from "@/components/ui/slider"
// Curseur

import { Label } from "@/components/ui/label"
// Étiquette formulaire

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
// Gestion formulaire React Hook Form
```

### 3.4 Data Display

```tsx
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
// Tableau

import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
// Palette commandes

import { Badge } from "@/components/ui/badge"
// Badge statut

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
// Avatar utilisateur

import { Calendar } from "@/components/ui/calendar"
// Calendrier
```

### 3.5 Feedback

```tsx
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
// Alerte utilisateur

import { Toast, ToastAction, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast"
// Notifications toast

import { Progress } from "@/components/ui/progress"
// Barre progression

import { Skeleton } from "@/components/ui/skeleton"
// Placeholder chargement

import { Sonner } from "@/components/ui/sonner"
// Bibliothèque toast
```

### 3.6 Overlays

```tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
// Boîte dialogue modale

import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
// Panneau latéral

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
// Popover

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
// Info-bulle

import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
// Carte survol

import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuSub, DropdownMenuSubContent, DropdownMenuSubTrigger, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
// Menu déroulant

import { ContextMenu, ContextMenuCheckboxItem, ContextMenuContent, ContextMenuItem, ContextMenuLabel, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger, ContextMenuTrigger } from "@/components/ui/context-menu"
// Menu contextuel

import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
// Dialogue alerte

import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger } from "@/components/ui/drawer"
// Tiroir
```

### 3.7 Misc

```tsx
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
// Contenu repliable

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
// Accordéon

import { Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarMenu, MenubarRadioGroup, MenubarRadioItem, MenubarSeparator, MenubarShortcut, MenubarSub, MenubarSubContent, MenubarSubTrigger, MenubarTrigger } from "@/components/ui/menubar"
// Barre menus

import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "@/components/ui/carousel"
// Carrousel

import { InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot } from "@/components/ui/input-otp"
// Code OTP

import { Chart, ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from "@/components/ui/chart"
// Graphiques
```

## 4. Structure Projet

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # ShadCN/UI components (47)
│   │   └── custom/          # Custom components
│   ├── pages/               # Route pages
│   ├── hooks/               # Custom hooks
│   ├── lib/                 # Utilities
│   ├── styles/
│   │   └── globals.css      # Tokens sémantiques
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## 5. Patterns Développement

### 5.1 Component Pattern

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface TaskCardProps {
  title: string
  content: string
  onEdit: () => void
}

export const TaskCard: React.FC<TaskCardProps> = ({ title, content, onEdit }) => (
  <Card className="bg-card border-border">
    <CardHeader>
      <CardTitle className="text-foreground">{title}</CardTitle>
    </CardHeader>
    <CardContent className="text-muted-foreground">
      {content}
      <Button
        onClick={onEdit}
        className="bg-primary text-primary-foreground hover:bg-accent"
      >
        Edit
      </Button>
    </CardContent>
  </Card>
)
```

### 5.2 Form Pattern

```tsx
import { useForm } from "react-hook-form"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export const TaskForm = () => {
  const form = useForm()

  return (
    <Form {...form}>
      <FormField
        control={form.control}
        name="title"
        render={({ field }) => (
          <FormItem>
            <FormLabel className="text-foreground">Title</FormLabel>
            <FormControl>
              <Input
                placeholder="Task title"
                className="bg-background border-input text-foreground"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <Button type="submit" className="bg-primary text-primary-foreground">
        Submit
      </Button>
    </Form>
  )
}
```

### 5.3 Layout Pattern

```tsx
import { Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarProvider } from "@/components/ui/sidebar"

export const AppLayout = ({ children }: { children: React.ReactNode }) => (
  <SidebarProvider>
    <div className="flex h-screen bg-background">
      <Sidebar className="bg-card border-r border-border">
        <SidebarHeader className="text-foreground">
          AGI App
        </SidebarHeader>
        <SidebarContent>
          <SidebarMenu>
            <SidebarMenuItem className="text-muted-foreground hover:bg-accent">
              Dashboard
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarContent>
      </Sidebar>
      <main className="flex-1 bg-muted p-4">
        {children}
      </main>
    </div>
  </SidebarProvider>
)
```

## 6. Configuration

### 6.1 Tailwind Config

```js
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
    },
  },
}
```

### 6.2 Globals CSS

```css
/* styles/globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;        /* #ffffff */
    --foreground: 0 0% 0%;          /* #000000 */
    --card: 0 0% 100%;              /* #ffffff */
    --card-foreground: 0 0% 0%;     /* #000000 */
    --muted: 240 5% 96%;            /* #f4f4f5 */
    --muted-foreground: 0 0% 45%;   /* #71717a */
    --accent: 240 5% 96%;           /* #f4f4f5 */
    --accent-foreground: 0 0% 0%;   /* #000000 */
    --primary: 0 0% 0%;             /* #000000 */
    --primary-foreground: 0 0% 100%; /* #ffffff */
    --secondary: 240 5% 96%;        /* #f4f4f5 */
    --secondary-foreground: 0 0% 0%; /* #000000 */
    --border: 240 6% 90%;           /* #e4e4e7 */
    --input: 240 6% 90%;            /* #e4e4e7 */
  }
}
```

## 7. Règles Strictes

### 7.1 TOUJOURS

✅ Utiliser tokens sémantiques (bg-background, text-foreground)
✅ Utiliser composants ShadCN/UI disponibles AVANT créer custom
✅ Palette noir/gris/blanc uniquement
✅ TypeScript strict mode
✅ Functional components `React.FC<Props>`
✅ Custom hooks pour logic réutilisable
✅ Props interfaces séparées des components

### 7.2 JAMAIS

❌ Classes hardcodées (bg-white, bg-gray-100, text-blue-500)
❌ Couleurs hex inline (style={{ color: '#000' }})
❌ Couleurs non-grayscale (rouge, bleu, vert)
❌ Components custom si ShadCN/UI existe
❌ Any types TypeScript
❌ Class components (toujours functional)

## 8. Installation

```bash
# Create React + Vite + TypeScript
npm create vite@latest frontend -- --template react-ts

# Install Tailwind
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install ShadCN/UI
npx shadcn-ui@latest init

# Add components (exemple)
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add form
```

## 9. Checklist Projet

- [ ] Vite + React 18 + TypeScript configuré
- [ ] Tailwind CSS installé avec config tokens
- [ ] globals.css avec variables CSS tokens
- [ ] ShadCN/UI initialisé
- [ ] Structure folders (components/ui, pages, hooks)
- [ ] tsconfig.json strict mode enabled
- [ ] Tous components utilisent tokens sémantiques
- [ ] Aucune couleur hardcodée présente
- [ ] ShadCN/UI composants utilisés prioritairement
- [ ] TypeScript interfaces définies pour props
- [ ] ESLint + Prettier configurés

## 10. Résumé

Convention Figma Make = système design strict + composants production-ready + tokens sémantiques pour cohérence maximale et maintenance facilitée long-terme.

**Priorité absolue** : Tokens sémantiques > Composants ShadCN/UI > Custom components.
