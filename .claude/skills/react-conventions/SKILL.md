---
name: react-conventions
description: Figma Make architecture COMPLÈTE - système design noir/gris/blanc strict AGI avec 47 composants ShadCN/UI
type: documentation
---

# REACT CONVENTIONS - FIGMA MAKE ARCHITECTURE

*Documentation complète pour le développement frontend avec Figma Make et système de design AGI*

## 1. Vue d'ensemble du système

### 1.1 Architecture Figma Make
Le projet AGI utilise l'architecture Figma Make, un système de construction d'applications web 0→1 basé sur React et Tailwind CSS. Cette architecture permet de créer des prototypes, maquettes et applications web fonctionnelles avec une approche composant-first.

### 1.2 Système de design AGI
Notre système de design suit une palette stricte **noir/gris/blanc** avec des tokens sémantiques pour garantir la cohérence visuelle et l'accessibilité.

### 1.3 Objectifs de ce document
- Définir les règles strictes de développement frontend
- Éviter les duplications et incohérences
- Maintenir la structure Figma Make existante
- Assurer la cohérence du système de design AGI

## 2. Système de couleurs strict

### 2.1 Palette de couleurs autorisée
**RÈGLE ABSOLUE : Utiliser UNIQUEMENT les tokens sémantiques**

```css
/* Tokens sémantiques disponibles dans styles/globals.css */
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

### 2.2 Hiérarchie visuelle (de la base aux overlays)
1. **Couche de base** : `bg-muted` (#f4f4f5) - Arrière-plan de page
2. **Couche de surface** : `bg-card` (#ffffff) - Panneaux, cartes
3. **États interactifs** : `bg-accent` (#f4f4f5) - Effets de survol
4. **Bordures** : `border-border` (#e4e4e7) - Diviseurs
5. **Hiérarchie de texte** :
   - Principal : `text-foreground` (#000000)
   - Secondaire : `text-muted-foreground` (#71717a)
   - Désactivé : `text-muted-foreground/50`

### 2.3 Classes interdites
```css
/* ❌ INTERDIT - Classes de couleurs hardcodées */
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

## 3. Composants ShadCN/UI disponibles (47 composants)

### 3.1 Composants de mise en page
```tsx
import { AspectRatio } from "./components/ui/aspect-ratio";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
import { Separator } from "./components/ui/separator";
import { ScrollArea } from "./components/ui/scroll-area";
import { Resizable, ResizableHandle, ResizablePanel, ResizablePanelGroup } from "./components/ui/resizable";
import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarMenuSub, SidebarMenuSubButton, SidebarMenuSubItem, SidebarProvider, SidebarRail, SidebarSeparator, SidebarTrigger } from "./components/ui/sidebar";
```

### 3.2 Composants de navigation
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Breadcrumb, BreadcrumbEllipsis, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "./components/ui/breadcrumb";
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "./components/ui/pagination";
import { NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger, NavigationMenuViewport } from "./components/ui/navigation-menu";
import { Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarMenu, MenubarRadioGroup, MenubarRadioItem, MenubarSeparator, MenubarShortcut, MenubarSub, MenubarSubContent, MenubarSubTrigger, MenubarTrigger } from "./components/ui/menubar";
```

### 3.3 Composants de formulaire
```tsx
import { Button, buttonVariants } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from "./components/ui/select";
import { Checkbox } from "./components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "./components/ui/radio-group";
import { Switch } from "./components/ui/switch";
import { Slider } from "./components/ui/slider";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "./components/ui/form";
import { InputOtp, InputOtpGroup, InputOtpSeparator, InputOtpSlot } from "./components/ui/input-otp";
```

### 3.4 Composants d'overlay et de dialogue
```tsx
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "./components/ui/sheet";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuPortal, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuSub, DropdownMenuSubContent, DropdownMenuSubTrigger, DropdownMenuTrigger } from "./components/ui/dropdown-menu";
import { ContextMenu, ContextMenuCheckboxItem, ContextMenuContent, ContextMenuGroup, ContextMenuItem, ContextMenuLabel, ContextMenuPortal, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger, ContextMenuTrigger } from "./components/ui/context-menu";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./components/ui/tooltip";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "./components/ui/hover-card";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./components/ui/alert-dialog";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerOverlay, DrawerPortal, DrawerTitle, DrawerTrigger } from "./components/ui/drawer";
```

### 3.5 Composants de feedback et d'état
```tsx
import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert";
import { Badge, badgeVariants } from "./components/ui/badge";
import { Progress } from "./components/ui/progress";
import { Skeleton } from "./components/ui/skeleton";
import { Sonner } from "./components/ui/sonner";
import { Toggle, toggleVariants } from "./components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "./components/ui/toggle-group";
```

### 3.6 Composants de données et de contenu
```tsx
import { Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "./components/ui/table";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./components/ui/accordion";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./components/ui/collapsible";
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut } from "./components/ui/command";
import { Calendar } from "./components/ui/calendar";
import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "./components/ui/carousel";
import { Chart, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "./components/ui/chart";
```

## 4. Règles d'utilisation des composants ShadCN

### 4.1 Import obligatoire
```tsx
// ✅ Format d'import correct
import { ComponentName } from "./components/ui/component-name";

// ❌ INTERDIT - Import depuis node_modules
import { ComponentName } from "@/components/ui/component-name";
import { ComponentName } from "shadcn/ui";
```

### 4.2 Modifications autorisées
```tsx
// ✅ Modifications mineures autorisées
<Button className="w-full">Texte du bouton</Button>
<Card className="border-2"><CardContent>...</CardContent></Card>

// ❌ INTERDIT - Créer des versions personnalisées
// Ne pas créer /components/ui/custom-button.tsx
// Ne pas réécrire les composants ShadCN existants
```

### 4.3 Répertoire protégé
```bash
# ❌ INTERDIT - Modifications dans /components/ui/
/components/ui/  # Réservé UNIQUEMENT aux composants ShadCN
├── button.tsx  # NE PAS MODIFIER
├── card.tsx    # NE PAS MODIFIER
└── ...         # NE PAS AJOUTER de nouveaux fichiers
```

## 5. Règles Tailwind CSS strictes

### 5.1 Classes de typographie interdites
```css
/* ❌ INTERDIT - Classes de taille de police */
text-xs, text-sm, text-base, text-lg, text-xl, text-2xl, text-3xl, text-4xl, text-5xl, text-6xl

/* ❌ INTERDIT - Classes de poids de police */
font-thin, font-extralight, font-light, font-normal, font-medium, font-semibold, font-bold, font-extrabold, font-black

/* ❌ INTERDIT - Classes de hauteur de ligne */
leading-none, leading-tight, leading-snug, leading-normal, leading-relaxed, leading-loose

/* ❌ INTERDIT - Classes de famille de police */
font-sans, font-serif, font-mono
```

### 5.2 Typographie par défaut (styles/globals.css)
```css
/* ✅ Typographie configurée dans globals.css - NE PAS OVERRIDE */
h1 { @apply text-2xl font-medium; }
h2 { @apply text-xl font-medium; }
h3 { @apply text-lg font-medium; }
p  { @apply text-base font-normal; }
button { @apply text-base font-medium; }
label { @apply text-base font-medium; }
small { @apply text-sm font-normal; }
```

### 5.3 Échelle d'espacement cohérente
```css
/* ✅ Espacement autorisé */
gap-1 gap-2 gap-3 gap-4 gap-6 gap-8 gap-12 gap-16
p-1 p-2 p-3 p-4 p-6 p-8 p-12 p-16
m-1 m-2 m-3 m-4 m-6 m-8 m-12 m-16
```

### 5.4 Classes utilitaires autorisées
```css
/* ✅ Layout */
flex grid block inline hidden
justify-center items-center flex-col flex-row
w-full h-full min-h-screen max-w-md

/* ✅ Espacement */
space-x-4 space-y-2 gap-4 p-4 m-2

/* ✅ Bordures (avec tokens sémantiques) */
border border-2 border-t border-b
rounded rounded-md rounded-lg rounded-full

/* ✅ États */
hover:bg-accent focus:ring-2 disabled:opacity-50
transition-colors duration-200 ease-in-out
```

## 6. Gestion des images et assets

### 6.1 Composant ImageWithFallback obligatoire
```tsx
// ✅ Import obligatoire pour les nouvelles images
import { ImageWithFallback } from './components/figma/ImageWithFallback';

// ✅ Utilisation correcte
<ImageWithFallback
  src="/path/to/image.jpg"
  alt="Description de l'image"
  width={300}
  height={200}
  className="rounded-lg"
/>

// ❌ INTERDIT - Balise img directe
<img src="/path/to/image.jpg" alt="..." />
```

### 6.2 Fichier protégé
```bash
# ❌ INTERDIT - Modification du composant
/components/figma/ImageWithFallback.tsx  # FICHIER PROTÉGÉ
```

### 6.3 Icônes avec Lucide React
```tsx
// ✅ Import et utilisation des icônes
import { Home, User, Settings, ChevronRight } from 'lucide-react';

// ✅ Icônes en noir uniquement
<Home className="w-5 h-5 text-foreground" />
<User className="w-4 h-4 text-muted-foreground" />

// ❌ INTERDIT - Icônes colorées
<Home className="w-5 h-5 text-blue-500" />
```

## 7. Librairies et versions spécifiques

### 7.1 Versions obligatoires
```tsx
// ✅ Versions spécifiques requises
import { useForm } from 'react-hook-form@7.55.0';
import { toast } from "sonner@2.0.3";

// ✅ Imports sans version (dernière version)
import { motion } from 'motion/react';
import { Icon } from 'lucide-react';
import { ResponsiveContainer, LineChart } from 'recharts';
```

### 7.2 Librairies recommandées
```tsx
// Animation
import { motion } from 'motion/react';

// Graphiques
import { LineChart, BarChart, PieChart } from 'recharts';

// Drag & Drop
import { DndContext, closestCenter } from '@dnd-kit/core';

// Carrousels
import Slider from 'react-slick';

// Grilles Masonry
import Masonry from 'react-responsive-masonry';

// Positionnement
import { usePopper } from 'react-popper';
```

### 7.3 Librairies interdites
```tsx
// ❌ INTERDIT
import { motion } from 'framer-motion';     // Utiliser motion/react
import { Resizable } from 'react-resizable'; // Utiliser re-resizable
import Konva from 'konva';                   // Utiliser canvas directement
```

## 8. Structure de fichiers et architecture

### 8.1 Point d'entrée obligatoire
```tsx
// ✅ /App.tsx - Point d'entrée principal
import React from 'react';
import { ComponentName } from './components/component-name';

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      {/* Contenu de l'application */}
    </div>
  );
}
```

### 8.2 Structure des composants
```bash
# ✅ Structure recommandée
/App.tsx
/components/
├── header.tsx
├── sidebar.tsx
├── time-block.tsx
└── ui/  # ❌ RÉSERVÉ aux composants ShadCN
    ├── button.tsx  # NE PAS MODIFIER
    └── card.tsx    # NE PAS MODIFIER

/components/figma/
└── ImageWithFallback.tsx  # NE PAS MODIFIER

/styles/
└── globals.css  # NE PAS MODIFIER (sauf tokens)
```

### 8.3 Conventions de nommage
```tsx
// ✅ Nommage des composants
export function TimeBlockCard() { ... }      // PascalCase
export function UserProfileSidebar() { ... } // PascalCase

// ✅ Nommage des fichiers
time-block-card.tsx          // kebab-case
user-profile-sidebar.tsx     // kebab-case

// ✅ Import des composants
import { TimeBlockCard } from './components/time-block-card';
```

## 9. Développement et bonnes pratiques

### 9.1 Approche composant-first
```tsx
// ✅ Préférer plusieurs composants
import { Header } from './components/header';
import { Sidebar } from './components/sidebar';
import { MainContent } from './components/main-content';

export default function App() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1">
        <Header />
        <MainContent />
      </div>
    </div>
  );
}
```

### 9.2 Gestion des états
```tsx
// ✅ États locaux avec useState
import { useState } from 'react';

function TimeBlockCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  return (
    <Card className={isExpanded ? 'h-auto' : 'h-32'}>
      {/* Contenu */}
    </Card>
  );
}

// ✅ Props typées avec TypeScript
interface TimeBlockProps {
  title: string;
  duration: number;
  isCompleted?: boolean;
}

function TimeBlock({ title, duration, isCompleted = false }: TimeBlockProps) {
  return (
    <div className="p-4 bg-card border border-border rounded-lg">
      <h3>{title}</h3>
      <span className="text-muted-foreground">{duration}min</span>
    </div>
  );
}
```

### 9.3 Gestion des listes et keys
```tsx
// ✅ Keys uniques pour les listes
const timeBlocks = [
  { id: '1', title: 'Réunion équipe', duration: 60 },
  { id: '2', title: 'Développement', duration: 120 },
];

return (
  <div className="space-y-4">
    {timeBlocks.map((block) => (
      <TimeBlock
        key={block.id}  // ✅ Key unique
        title={block.title}
        duration={block.duration}
      />
    ))}
  </div>
);

// ❌ Keys non-uniques
{timeBlocks.map((block, index) => (
  <TimeBlock key={index} {...block} />
))}
```

### 9.4 Gestion des formulaires
```tsx
// ✅ Formulaires avec React Hook Form
import { useForm } from 'react-hook-form@7.55.0';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';

interface FormData {
  title: string;
  duration: number;
}

function CreateTimeBlockForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();

  const onSubmit = (data: FormData) => {
    console.log(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Label htmlFor="title">Titre</Label>
        <Input
          id="title"
          {...register('title', { required: 'Le titre est requis' })}
        />
        {errors.title && (
          <span className="text-destructive text-sm">{errors.title.message}</span>
        )}
      </div>
      <Button type="submit">Créer</Button>
    </form>
  );
}
```

## 10. Animations et interactions

### 10.1 Animations avec Motion
```tsx
// ✅ Import et utilisation de Motion
import { motion } from 'motion/react';

function AnimatedCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="p-6 bg-card border border-border rounded-lg"
    >
      <h3>Contenu animé</h3>
    </motion.div>
  );
}

// ✅ Animations de hover
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.98 }}
  className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
>
  Bouton animé
</motion.button>
```

### 10.2 Transitions CSS
```tsx
// ✅ Transitions avec classes Tailwind
<div className="transition-colors duration-200 hover:bg-accent">
  Contenu avec transition
</div>

// ✅ États interactifs
<Button className="hover:bg-accent focus:ring-2 focus:ring-primary">
  Bouton interactif
</Button>
```

### 10.3 États de chargement
```tsx
// ✅ Skeleton pour le chargement
import { Skeleton } from './components/ui/skeleton';

function LoadingTimeBlock() {
  return (
    <div className="p-4 space-y-3">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-4 w-1/2" />
      <Skeleton className="h-8 w-full" />
    </div>
  );
}

// ✅ États conditionnels
function TimeBlockList({ isLoading, timeBlocks }) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <LoadingTimeBlock key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {timeBlocks.map(block => (
        <TimeBlock key={block.id} {...block} />
      ))}
    </div>
  );
}
```

## 11. Responsive Design et accessibilité

### 11.1 Design responsive
```tsx
// ✅ Classes responsive
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Grille responsive */}
</div>

// ✅ Espacement responsive
<div className="p-4 md:p-6 lg:p-8">
  {/* Padding responsive */}
</div>
```

### 11.2 Accessibilité
```tsx
// ✅ Labels et ARIA
<Label htmlFor="email">Email</Label>
<Input
  id="email"
  type="email"
  aria-describedby="email-error"
/>
<span id="email-error" className="text-destructive">
  Email invalide
</span>

// ✅ Navigation au clavier
<Button
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Bouton accessible
</Button>

// ✅ Contraste et focus
<Button className="focus:ring-2 focus:ring-primary focus:ring-offset-2">
  Bouton avec focus visible
</Button>
```

### 11.3 Sémantique HTML
```tsx
// ✅ Structure sémantique
<main className="flex-1">
  <header className="border-b border-border">
    <h1>Titre principal</h1>
  </header>

  <section className="p-6">
    <h2>Section de contenu</h2>
    <article className="bg-card p-4 rounded-lg">
      <h3>Article</h3>
      <p>Contenu de l'article</p>
    </article>
  </section>
</main>
```

## 12. Gestion des erreurs et feedback

### 12.1 Notifications toast
```tsx
// ✅ Toast avec Sonner
import { toast } from "sonner@2.0.3";

function handleSave() {
  try {
    toast.success("Sauvegardé avec succès");
  } catch (error) {
    toast.error("Erreur lors de la sauvegarde");
  }
}

// ✅ Configuration du toast provider
import { Toaster } from './components/ui/sonner';

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      {/* Contenu */}
      <Toaster />
    </div>
  );
}
```

### 12.2 Gestion des erreurs
```tsx
// ✅ États d'erreur
interface TimeBlockState {
  data: TimeBlock[];
  loading: boolean;
  error: string | null;
}

function TimeBlockContainer() {
  const [state, setState] = useState<TimeBlockState>({
    data: [],
    loading: false,
    error: null
  });

  if (state.error) {
    return (
      <Alert className="border-destructive">
        <AlertTitle>Erreur</AlertTitle>
        <AlertDescription>{state.error}</AlertDescription>
      </Alert>
    );
  }

  return <div>{/* Contenu normal */}</div>;
}
```

### 12.3 Validation de formulaires
```tsx
// ✅ Validation avec messages d'erreur
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({
  title: z.string().min(1, 'Le titre est requis'),
  duration: z.number().min(1, 'La durée doit être positive')
});

function CreateForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema)
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <Input {...register('title')} />
        {errors.title && (
          <span className="text-destructive text-sm">
            {errors.title.message}
          </span>
        )}
      </div>
    </form>
  );
}
```

## 13. Performance et optimisation

### 13.1 Lazy loading des composants
```tsx
// ✅ Lazy loading avec React.lazy
import { lazy, Suspense } from 'react';
import { Skeleton } from './components/ui/skeleton';

const HeavyComponent = lazy(() => import('./components/heavy-component'));

function App() {
  return (
    <div>
      <Suspense fallback={<Skeleton className="h-64 w-full" />}>
        <HeavyComponent />
      </Suspense>
    </div>
  );
}
```

### 13.2 Mémorisation avec useMemo et useCallback
```tsx
// ✅ Optimisation des calculs coûteux
import { useMemo, useCallback } from 'react';

function TimeBlockList({ timeBlocks, filter }) {
  const filteredBlocks = useMemo(() => {
    return timeBlocks.filter(block =>
      block.title.toLowerCase().includes(filter.toLowerCase())
    );
  }, [timeBlocks, filter]);

  const handleBlockClick = useCallback((blockId: string) => {
    // Logique de clic
  }, []);

  return (
    <div>
      {filteredBlocks.map(block => (
        <TimeBlock
          key={block.id}
          {...block}
          onClick={() => handleBlockClick(block.id)}
        />
      ))}
    </div>
  );
}
```

### 13.3 Optimisation des images
```tsx
// ✅ Images optimisées avec ImageWithFallback
import { ImageWithFallback } from './components/figma/ImageWithFallback';

function UserAvatar({ src, alt, size = 40 }) {
  return (
    <ImageWithFallback
      src={src}
      alt={alt}
      width={size}
      height={size}
      className="rounded-full object-cover"
      loading="lazy"
    />
  );
}
```

## 14. Tests et qualité du code

### 14.1 Types TypeScript stricts
```tsx
// ✅ Interfaces strictes
interface TimeBlock {
  id: string;
  title: string;
  duration: number;
  startTime: Date;
  isCompleted: boolean;
  category?: 'work' | 'personal' | 'break';
}

// ✅ Props typées
interface TimeBlockCardProps {
  timeBlock: TimeBlock;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  className?: string;
}

// ❌ Éviter any
function BadComponent(props: any) { ... }  // ❌
function GoodComponent(props: TimeBlockCardProps) { ... }  // ✅
```

### 14.2 Gestion des cas d'erreur
```tsx
// ✅ Gestion défensive
function TimeBlockCard({ timeBlock, onEdit, onDelete }: TimeBlockCardProps) {
  if (!timeBlock) {
    return null;
  }

  const handleEdit = () => {
    if (onEdit) {
      onEdit(timeBlock.id);
    }
  };

  return (
    <Card>
      <CardContent>
        <h3>{timeBlock.title}</h3>
        <Button onClick={handleEdit} disabled={!onEdit}>
          Modifier
        </Button>
      </CardContent>
    </Card>
  );
}
```

## 15. Common Mistakes to Avoid

### 15.1 Erreurs de couleurs
```tsx
// ❌ DON'T: Couleurs hardcodées
<div className="bg-white text-black border-gray-200">Contenu</div>

// ❌ DON'T: Couleurs non-grayscale
<div className="bg-blue-500 text-white">Bouton bleu</div>

// ✅ DO: Tokens sémantiques
<div className="bg-card text-foreground border-border">Contenu</div>
```

### 15.2 Erreurs de typographie
```tsx
// ❌ DON'T: Classes de typographie
<h1 className="text-3xl font-bold">Titre</h1>

// ✅ DO: Utiliser la typographie par défaut
<h1>Titre</h1>
<p className="text-muted-foreground">Texte</p>
```

### 15.3 Erreurs de structure
```tsx
// ❌ DON'T: Créer des composants ShadCN personnalisés
export function CustomButton() { ... }

// ❌ DON'T: Import incorrect
import { Button } from '@/components/ui/button';

// ✅ DO: Import correct
import { Button } from './components/ui/button';
```

### 15.4 Erreurs d'images
```tsx
// ❌ DON'T: Balise img directe
<img src="/avatar.jpg" alt="Avatar" />

// ✅ DO: Utiliser ImageWithFallback
import { ImageWithFallback } from './components/figma/ImageWithFallback';
<ImageWithFallback
  src="/avatar.jpg"
  alt="Avatar utilisateur"
  width={40}
  height={40}
  className="rounded-full"
/>
```

### 15.5 Erreurs de librairies
```tsx
// ❌ DON'T: Anciennes librairies
import { motion } from 'framer-motion';
import { useForm } from 'react-hook-form';  // Manque @7.55.0
import { toast } from 'sonner';             // Manque @2.0.3

// ✅ DO: Versions correctes
import { motion } from 'motion/react';
import { useForm } from 'react-hook-form@7.55.0';
import { toast } from 'sonner@2.0.3';
```

### 15.6 Erreurs de développement
```tsx
// ❌ DON'T: Placeholders
<h1>Titre</h1>
{/* TODO: Ajouter le contenu */}

// ❌ DON'T: Keys non-uniques
{items.map((item, index) => (
  <div key={index}>{item.name}</div>
))}

// ✅ DO: Implémentation complète
{items.map((item) => (
  <div key={item.id}>{item.name}</div>
))}
```

### 15.7 Erreurs de responsive
```tsx
// ❌ DON'T: Design non-responsive
<div className="w-800 h-600">Contenu</div>

// ✅ DO: Design responsive
<div className="w-full max-w-4xl mx-auto">
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
    Grille responsive
  </div>
</div>
```

### 15.8 Erreurs d'accessibilité
```tsx
// ❌ DON'T: Manque d'accessibilité
<div onClick={handleClick}>Bouton</div>
<input />

// ✅ DO: Accessibilité complète
<Button onClick={handleClick}>Bouton accessible</Button>
<Label htmlFor="input">Label</Label>
<Input id="input" />
```

## 16. Prompt système pour l'agent de codage frontend

Tu es l'agent de codage frontend pour le projet AGI Time Blocking. Tu DOIS respecter strictement la structure Figma Make existante et le système de design noir/gris/blanc.

**RÈGLES ABSOLUES - AUCUNE EXCEPTION:**

**1. COULEURS STRICTES:**
   - Utilise UNIQUEMENT les tokens sémantiques: bg-background, bg-card, bg-muted, bg-accent, bg-primary
   - Texte: text-foreground, text-muted-foreground, text-primary-foreground
   - Bordures: border-border, border-input
   - INTERDIT: bg-white, bg-black, bg-gray-*, text-blue-*, border-red-*, couleurs hex

**2. COMPOSANTS SHADCN/UI:**
   - Utilise UNIQUEMENT les 47 composants existants dans /components/ui/
   - Import: import { Component } from './components/ui/component'
   - JAMAIS créer de composants dans /components/ui/
   - JAMAIS modifier les composants ShadCN existants

**3. STRUCTURE OBLIGATOIRE:**
   - App.tsx est le point d'entrée avec export default
   - Composants personnalisés dans /components/ uniquement
   - JAMAIS modifier /components/ui/ ou /styles/globals.css
   - JAMAIS modifier /components/figma/ImageWithFallback.tsx

**4. TYPOGRAPHIE:**
   - INTERDIT: text-xl, font-bold, leading-none (sauf demande explicite)
   - Utilise la typographie par défaut de globals.css
   - h1, h2, h3, p, button ont des styles prédéfinis

**5. IMAGES:**
   - Utilise ImageWithFallback pour les nouvelles images
   - Import: import { ImageWithFallback } from './components/figma/ImageWithFallback'
   - JAMAIS utiliser <img> directement

**6. LIBRAIRIES:**
   - Versions spécifiques: react-hook-form@7.55.0, sonner@2.0.3
   - Motion: import { motion } from 'motion/react'
   - Icônes: import { Icon } from 'lucide-react'

**7. DÉVELOPPEMENT:**
   - JAMAIS de placeholders (// TODO, // Rest of code)
   - Keys uniques pour les listes (pas d'index)
   - TypeScript strict avec interfaces
   - Gestion d'erreurs complète

En cas de doute, DEMANDE confirmation avant de modifier la structure existante.

## 17. Exemples d'implémentation complète

### 17.1 Composant de carte de temps
```tsx
// /components/time-block-card.tsx
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Clock, Edit, Trash2 } from 'lucide-react';

interface TimeBlockCardProps {
  id: string;
  title: string;
  duration: number;
  startTime: Date;
  isCompleted: boolean;
  category: 'work' | 'personal' | 'break';
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function TimeBlockCard({
  id, title, duration, startTime, isCompleted, category, onEdit, onDelete
}: TimeBlockCardProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  };

  const getCategoryLabel = (cat: string) => {
    const labels = { work: 'Travail', personal: 'Personnel', break: 'Pause' };
    return labels[cat] || cat;
  };

  return (
    <Card className={isCompleted ? 'bg-muted' : 'bg-card'}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className={isCompleted ? 'text-muted-foreground line-through' : 'text-foreground'}>
            {title}
          </CardTitle>
          <Badge variant="secondary">{getCategoryLabel(category)}</Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-muted-foreground">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{formatTime(startTime)}</span>
            </div>
            <span>{duration} min</span>
          </div>
          <div className="flex items-center gap-2">
            {onEdit && (
              <Button variant="ghost" size="sm" onClick={() => onEdit(id)} className="h-8 w-8 p-0">
                <Edit className="w-4 h-4" />
              </Button>
            )}
            {onDelete && (
              <Button variant="ghost" size="sm" onClick={() => onDelete(id)} className="h-8 w-8 p-0 hover:bg-destructive">
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 17.2 Formulaire de création
```tsx
// /components/create-time-block-form.tsx
import React from 'react';
import { useForm } from 'react-hook-form@7.55.0';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner@2.0.3';

const schema = z.object({
  title: z.string().min(1, 'Le titre est requis'),
  duration: z.number().min(1, 'La durée doit être positive'),
  startTime: z.string().min(1, 'L\'heure de début est requise'),
  category: z.enum(['work', 'personal', 'break'])
});

type FormData = z.infer<typeof schema>;

interface CreateTimeBlockFormProps {
  onSubmit: (data: FormData) => void;
  onCancel?: () => void;
}

export function CreateTimeBlockForm({ onSubmit, onCancel }: CreateTimeBlockFormProps) {
  const { register, handleSubmit, setValue, watch, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { category: 'work' }
  });

  const handleFormSubmit = async (data: FormData) => {
    try {
      await onSubmit(data);
      toast.success('Bloc de temps créé avec succès');
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Nouveau bloc de temps</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="title">Titre</Label>
            <Input id="title" {...register('title')} placeholder="Ex: Réunion équipe" />
            {errors.title && <span className="text-destructive text-sm">{errors.title.message}</span>}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="duration">Durée (minutes)</Label>
              <Input id="duration" type="number" {...register('duration', { valueAsNumber: true })} placeholder="60" />
              {errors.duration && <span className="text-destructive text-sm">{errors.duration.message}</span>}
            </div>
            <div>
              <Label htmlFor="startTime">Heure de début</Label>
              <Input id="startTime" type="time" {...register('startTime')} />
              {errors.startTime && <span className="text-destructive text-sm">{errors.startTime.message}</span>}
            </div>
          </div>
          <div>
            <Label>Catégorie</Label>
            <Select value={watch('category')} onValueChange={(value) => setValue('category', value as any)}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner une catégorie" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="work">Travail</SelectItem>
                <SelectItem value="personal">Personnel</SelectItem>
                <SelectItem value="break">Pause</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            {onCancel && <Button type="button" variant="outline" onClick={onCancel}>Annuler</Button>}
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Création...' : 'Créer'}</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
```

### 17.3 Layout principal avec sidebar
```tsx
// /components/main-layout.tsx
import React, { useState } from 'react';
import { Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarProvider, SidebarTrigger } from './ui/sidebar';
import { Button } from './ui/button';
import { Calendar, Clock, Settings, Plus } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [activeView, setActiveView] = useState('calendar');

  const menuItems = [
    { id: 'calendar', label: 'Calendrier', icon: Calendar },
    { id: 'timeblocks', label: 'Blocs de temps', icon: Clock },
    { id: 'settings', label: 'Paramètres', icon: Settings },
  ];

  return (
    <SidebarProvider>
      <div className="flex min-h-screen bg-background">
        <Sidebar>
          <SidebarHeader className="border-b border-border">
            <div className="flex items-center gap-2 px-4 py-3">
              <Clock className="w-6 h-6 text-primary" />
              <span className="font-medium">AGI Time Blocking</span>
            </div>
          </SidebarHeader>
          <SidebarContent>
            <SidebarMenu>
              {menuItems.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton onClick={() => setActiveView(item.id)} className={activeView === item.id ? 'bg-accent' : ''}>
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
            <div className="mt-auto p-4">
              <Button className="w-full" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Nouveau bloc
              </Button>
            </div>
          </SidebarContent>
        </Sidebar>

        <div className="flex-1">
          <header className="border-b border-border bg-card">
            <div className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-4">
                <SidebarTrigger />
                <h1 className="text-xl font-semibold">
                  {activeView === 'calendar' && 'Calendrier'}
                  {activeView === 'timeblocks' && 'Blocs de temps'}
                  {activeView === 'settings' && 'Paramètres'}
                </h1>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">Synchroniser</Button>
                <Button size="sm"><Plus className="w-4 h-4 mr-2" />Nouveau</Button>
              </div>
            </div>
          </header>

          <main className="flex-1 p-6">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
```

## 18. Checklist de validation

Avant chaque commit, vérifier:

- [ ] Aucune couleur hardcodée (bg-white, text-black, etc.)
- [ ] Aucune classe de typographie non-autorisée
- [ ] Imports ShadCN corrects (./components/ui/)
- [ ] ImageWithFallback utilisé pour les images
- [ ] Aucun fichier créé dans /components/ui/
- [ ] Aucune modification des fichiers protégés
- [ ] Keys uniques pour toutes les listes
- [ ] Types TypeScript stricts
- [ ] Aucun placeholder dans le code
- [ ] Accessibilité respectée (labels, ARIA)

---

**Skill complet - Version finale**
**Document complet avec 47 composants ShadCN/UI**
**Lignes totales:** 1,940
**Dernière mise à jour:** 27 octobre 2025
