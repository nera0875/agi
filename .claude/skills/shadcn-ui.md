---
name: shadcn/ui Guidelines
description: Strict shadcn/ui component rules - always use ui/, never custom components
---

# shadcn/ui Mastery

Expertise shadcn/ui pour agents frontend - Composants UI modernes avec Radix UI primitives.

## Règles Strictes (NON-NÉGOCIABLES)

### JAMAIS Faire
- ❌ JAMAIS modifier tailwind.config.js
- ❌ JAMAIS créer composants custom UI (shadcn/ui existe déjà)
- ❌ JAMAIS classes font-size/weight inline (utiliser globals.css only)
- ❌ JAMAIS utiliser Framer Motion (utiliser motion/react)
- ❌ JAMAIS react-resizable (utiliser re-resizable)
- ❌ JAMAIS placeholder comments

### TOUJOURS Faire
- ✅ TOUJOURS utiliser composants shadcn/ui disponibles
- ✅ TOUJOURS TypeScript strict (types pour props)
- ✅ TOUJOURS accessibility WCAG 2.1 AA (ARIA labels)
- ✅ TOUJOURS préserver classes Tailwind existantes
- ✅ TOUJOURS importer depuis `@/components/ui/`
- ✅ TOUJOURS responsive design

## Composants Disponibles (shadcn/ui)

**Ne JAMAIS recréer - Utiliser directement:**

- Accordion
- Alert
- Avatar
- Badge
- Button
- Card
- Checkbox
- Command
- Dialog
- Dropdown Menu
- Form
- Input
- Label
- Popover
- Select
- Separator
- Sheet
- Skeleton
- Slider
- Switch
- Table
- Tabs
- Textarea
- Toast
- Tooltip

**Si composant manque:**
```bash
cd frontend
npx shadcn@latest add [component-name]
```

## Intégration Correcte

### Import Standard
```tsx
// ✅ CORRECT
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'  // Icons ONLY

// ❌ INCORRECT
import Button from './button'  // Custom import
import { motion } from 'framer-motion'  // Wrong lib
```

### Architecture Composant
```tsx
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Database } from 'lucide-react'

interface ComponentNameProps {
  title: string
  onAction: () => void
}

export function ComponentName({ title, onAction }: ComponentNameProps) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2">
        <Database className="w-5 h-5" />
        <h2>{title}</h2>
      </div>
      <Button onClick={onAction}>Action</Button>
    </Card>
  )
}
```

## Patterns Standards d'Utilisation

### Validation & Réponse d'Erreur
```tsx
import { Alert } from '@/components/ui/alert'

// Pour les erreurs
<Alert variant="destructive">
  <AlertCircle className="w-4 h-4" />
  <p>Message d'erreur</p>
</Alert>

// Pour l'état de chargement
<Skeleton className="w-full h-10" />
```

### Toasts & Notifications
```tsx
import { toast } from 'sonner'

// Succès
toast.success("Opération réussie")

// Erreur
toast.error("Une erreur s'est produite")

// Info
toast.info("Information")
```

### Tables avec TanStack
```tsx
import { Button } from '@/components/ui/button'
import { useReactTable, getCoreRowModel } from '@tanstack/react-table'

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  enableRowSelection: true,
  enableColumnResizing: true,
})
```

### Forms avec react-hook-form
```tsx
import { useForm } from 'react-hook-form'
import { Form, FormField, FormItem } from '@/components/ui/form'

const form = useForm()
// Validation automatique + submission
```

## Exemples Concrets

### Exemple 1: Card Simple
```tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function MemoryCard({ title, content }: { title: string; content: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{content}</p>
        <Button className="mt-4">Voir plus</Button>
      </CardContent>
    </Card>
  )
}
```

### Exemple 2: Dialog avec Validation
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export function CreateDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Créer nouvel élément</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Input placeholder="Nom" />
          <Button className="w-full">Créer</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### Exemple 3: Erreurs à Éviter
```tsx
// ❌ MAUVAIS
import { motion } from 'framer-motion'
<div className="text-lg font-bold">Texte</div>
import ResizablePanel from 'react-resizable'
function CustomButton() { return <button>Click</button> }

// ✅ BON
import { motion } from 'motion/react'
<h2 className="text-lg font-bold">Texte</h2>
import { Resizable } from 're-resizable'
import { Button } from '@/components/ui/button'
<Button>Click</Button>
```

## Checklist Pre-Commit

Avant de créer/modifier composant:

- [ ] TypeScript compile sans erreurs
- [ ] Props complètement typées
- [ ] Utilisé shadcn/ui (jamais custom)
- [ ] Classes Tailwind CSS v4.0
- [ ] ARIA labels pour accessibilité
- [ ] Responsive design mobile-first
- [ ] Error handling correct
- [ ] Pas de placeholder comments
- [ ] Import depuis `@/components/ui/`
- [ ] Icons depuis `lucide-react` ONLY

## Ressources

**Guidelines Strictes:**
- Lire `/frontend/src/guidelines/figma.md` avant tout (30+ règles)
- Lire `/frontend/src/guidelines/*.md` pour contexte spécifique

**Documentation:**
- shadcn/ui: https://ui.shadcn.com/
- Radix UI: https://www.radix-ui.com/
- Tailwind CSS v4.0: https://tailwindcss.com/

**Tech Stack Complet:**
- React 18.3.1 + Vite 6.3.5
- TypeScript strict
- @apollo/client (GraphQL)
- @tanstack/react-table (tables)
- motion/react (animations)
- sonner (toasts)
- lucide-react (icons)
- re-resizable (resizing)
- react-dnd (drag-drop)
