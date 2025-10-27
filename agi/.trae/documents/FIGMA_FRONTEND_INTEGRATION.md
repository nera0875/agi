# FIGMA FRONTEND INTEGRATION - AGI Time Blocking
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

## 3. Composants ShadCN/UI disponibles

### 3.1 Liste complète des 47 composants

#### 3.1.1 Composants de mise en page
```tsx
// Layout & Structure
import { AspectRatio } from "./components/ui/aspect-ratio";
// Affiche le contenu dans un ratio désiré

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./components/ui/card";
// Affiche une carte avec en-tête, contenu et pied de page

import { Separator } from "./components/ui/separator";
// Sépare visuellement ou sémantiquement le contenu

import { ScrollArea } from "./components/ui/scroll-area";
// Améliore la fonctionnalité de défilement native avec un style personnalisé

import { Resizable, ResizableHandle, ResizablePanel, ResizablePanelGroup } from "./components/ui/resizable";
// Groupes de panneaux redimensionnables accessibles avec support clavier

import { Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader, SidebarInset, SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarMenuSub, SidebarMenuSubButton, SidebarMenuSubItem, SidebarProvider, SidebarRail, SidebarSeparator, SidebarTrigger } from "./components/ui/sidebar";
// Composant de barre latérale composable, thématisable et personnalisable
```

#### 3.1.2 Composants de navigation
```tsx
// Navigation
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
// Ensemble de sections de contenu en couches - panneaux d'onglets - affichés un à la fois

import { Breadcrumb, BreadcrumbEllipsis, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "./components/ui/breadcrumb";
// Affiche le chemin vers la ressource actuelle en utilisant une hiérarchie de liens

import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "./components/ui/pagination";
// Pagination avec navigation de page, liens suivant et précédent

import { NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuItem, NavigationMenuLink, NavigationMenuList, NavigationMenuTrigger, NavigationMenuViewport } from "./components/ui/navigation-menu";
// Collection de liens pour naviguer sur les sites web

import { Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarMenu, MenubarRadioGroup, MenubarRadioItem, MenubarSeparator, MenubarShortcut, MenubarSub, MenubarSubContent, MenubarSubTrigger, MenubarTrigger } from "./components/ui/menubar";
// Menu visuellement persistant commun dans les applications de bureau
```

#### 3.1.3 Composants de formulaire
```tsx
// Form Controls
import { Button, buttonVariants } from "./components/ui/button";
// Affiche un bouton ou un composant qui ressemble à un bouton

import { Input } from "./components/ui/input";
// Affiche un champ de saisie de formulaire ou un composant qui ressemble à un champ de saisie

import { Label } from "./components/ui/label";
// Rend une étiquette accessible associée aux contrôles

import { Textarea } from "./components/ui/textarea";
// Affiche une zone de texte de formulaire ou un composant qui ressemble à une zone de texte

import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue } from "./components/ui/select";
// Affiche une liste d'options que l'utilisateur peut choisir - déclenché par un bouton

import { Checkbox } from "./components/ui/checkbox";
// Contrôle qui permet à l'utilisateur de basculer entre coché et non coché

import { RadioGroup, RadioGroupItem } from "./components/ui/radio-group";
// Ensemble de boutons cochables - boutons radio - où pas plus d'un bouton peut être coché à la fois

import { Switch } from "./components/ui/switch";
// Contrôle qui permet à l'utilisateur de basculer entre activé et désactivé

import { Slider } from "./components/ui/slider";
// Entrée où l'utilisateur sélectionne une valeur dans une plage donnée

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "./components/ui/form";
// Construction de formulaires avec React Hook Form et Zod

import { InputOtp, InputOtpGroup, InputOtpSeparator, InputOtpSlot } from "./components/ui/input-otp";
// Composant de mot de passe à usage unique accessible avec fonctionnalité de copier-coller
```

#### 3.1.4 Composants d'overlay et de dialogue
```tsx
// Overlays & Dialogs
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
// Fenêtre superposée sur la fenêtre principale ou une autre fenêtre de dialogue

import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle, SheetTrigger } from "./components/ui/sheet";
// Étend le composant Dialog pour afficher du contenu qui complète le contenu principal de l'écran

import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
// Affiche du contenu riche dans un portail, déclenché par un bouton

import { DropdownMenu, DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuPortal, DropdownMenuRadioGroup, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuSub, DropdownMenuSubContent, DropdownMenuSubTrigger, DropdownMenuTrigger } from "./components/ui/dropdown-menu";
// Affiche un menu à l'utilisateur - ensemble d'actions ou de fonctions - déclenché par un bouton

import { ContextMenu, ContextMenuCheckboxItem, ContextMenuContent, ContextMenuGroup, ContextMenuItem, ContextMenuLabel, ContextMenuPortal, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger, ContextMenuTrigger } from "./components/ui/context-menu";
// Affiche un menu à l'utilisateur - ensemble d'actions ou de fonctions - déclenché par un bouton

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./components/ui/tooltip";
// Popup qui affiche des informations liées à un élément quand l'élément reçoit le focus clavier ou la souris survole

import { HoverCard, HoverCardContent, HoverCardTrigger } from "./components/ui/hover-card";
// Pour les utilisateurs voyants pour prévisualiser le contenu disponible derrière un lien

import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./components/ui/alert-dialog";
// Dialogue modal qui interrompt l'utilisateur avec du contenu important et attend une réponse

import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerOverlay, DrawerPortal, DrawerTitle, DrawerTrigger } from "./components/ui/drawer";
// Pour les panneaux coulissants
```

#### 3.1.5 Composants de feedback et d'état
```tsx
// Feedback & Status
import { Alert, AlertDescription, AlertTitle } from "./components/ui/alert";
// Pour les messages de notification

import { Badge, badgeVariants } from "./components/ui/badge";
// Affiche un badge ou un composant qui ressemble à un badge

import { Progress } from "./components/ui/progress";
// Affiche un indicateur montrant le progrès d'achèvement d'une tâche

import { Skeleton } from "./components/ui/skeleton";
// Utiliser pour montrer un placeholder pendant que le contenu se charge

import { Sonner } from "./components/ui/sonner";
// Pour les notifications toast

import { Toggle, toggleVariants } from "./components/ui/toggle";
// Bouton à deux états qui peut être activé ou désactivé

import { ToggleGroup, ToggleGroupItem } from "./components/ui/toggle-group";
// Ensemble de boutons à deux états qui peuvent être basculés activés ou désactivés
```

#### 3.1.6 Composants de données et de contenu
```tsx
// Data & Content
import { Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "./components/ui/table";
// Composant de tableau responsive

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./components/ui/accordion";
// Ensemble empilé verticalement d'en-têtes interactifs qui révèlent chacun une section de contenu

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./components/ui/collapsible";
// Composant interactif qui développe/réduit un panneau

import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut } from "./components/ui/command";
// Menu de commande rapide, composable et non stylé pour React

import { Calendar } from "./components/ui/calendar";
// Composant de champ de date qui permet aux utilisateurs d'entrer et d'éditer une date

import { Avatar, AvatarFallback, AvatarImage } from "./components/ui/avatar";
// Élément d'image avec un fallback pour représenter l'utilisateur

import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from "./components/ui/carousel";
// Carrousel avec mouvement et balayage construit avec Embla

import { Chart, ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, ChartTooltipContent } from "./components/ui/chart";
// Beaux graphiques. Construits avec Recharts. Copier et coller dans vos applications
```

### 3.2 Règles d'utilisation des composants ShadCN

#### 3.2.1 Import obligatoire
```tsx
// ✅ Format d'import correct
import { ComponentName } from "./components/ui/component-name";

// ❌ INTERDIT - Import depuis node_modules
import { ComponentName } from "@/components/ui/component-name";
import { ComponentName } from "shadcn/ui";
```

#### 3.2.2 Modifications autorisées
```tsx
// ✅ Modifications mineures autorisées
<Button className="w-full">  {/* Ajout de classes utilitaires */}
  Texte du bouton
</Button>

// ✅ Props personnalisées
<Card className="border-2">  {/* Modification de bordure */}
  <CardContent>...</CardContent>
</Card>

// ❌ INTERDIT - Créer des versions personnalisées
// Ne pas créer /components/ui/custom-button.tsx
// Ne pas réécrire les composants ShadCN existants
```

#### 3.2.3 Répertoire protégé
```bash
# ❌ INTERDIT - Modifications dans /components/ui/
/components/ui/  # Réservé UNIQUEMENT aux composants ShadCN
├── button.tsx  # NE PAS MODIFIER
├── card.tsx    # NE PAS MODIFIER
└── ...         # NE PAS AJOUTER de nouveaux fichiers
```

## 4. Règles Tailwind CSS strictes

### 4.1 Classes de typographie interdites
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

### 4.2 Typographie par défaut (styles/globals.css)
```css
/* ✅ Typographie configurée dans globals.css - NE PAS OVERRIDE */
h1 { @apply text-2xl font-medium; }      /* 24px, medium */
h2 { @apply text-xl font-medium; }       /* 20px, medium */
h3 { @apply text-lg font-medium; }       /* 18px, medium */
p  { @apply text-base font-normal; }     /* 16px, normal */
button { @apply text-base font-medium; } /* 16px, medium */
label { @apply text-base font-medium; }  /* 16px, medium */
small { @apply text-sm font-normal; }    /* 14px, normal */
```

### 4.3 Échelle d'espacement cohérente
```css
/* ✅ Espacement autorisé */
gap-1    /* 4px */
gap-2    /* 8px */
gap-3    /* 12px */
gap-4    /* 16px */
gap-6    /* 24px */
gap-8    /* 32px */
gap-12   /* 48px */
gap-16   /* 64px */

/* Padding/Margin identiques */
p-1, p-2, p-3, p-4, p-6, p-8, p-12, p-16
m-1, m-2, m-3, m-4, m-6, m-8, m-12, m-16
```

### 4.4 Classes utilitaires autorisées
```css
/* ✅ Layout */
flex, grid, block, inline, hidden
justify-center, items-center, flex-col, flex-row
w-full, h-full, min-h-screen, max-w-md

/* ✅ Espacement */
space-x-4, space-y-2, gap-4, p-4, m-2

/* ✅ Bordures (avec tokens sémantiques) */
border, border-2, border-t, border-b
rounded, rounded-md, rounded-lg, rounded-full

/* ✅ États */
hover:bg-accent, focus:ring-2, disabled:opacity-50
transition-colors, duration-200, ease-in-out
```

## 5. Gestion des images et assets

### 5.1 Composant ImageWithFallback obligatoire
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

### 5.2 Fichier protégé
```bash
# ❌ INTERDIT - Modification du composant
/components/figma/ImageWithFallback.tsx  # FICHIER PROTÉGÉ
```

### 5.3 Import d'assets Figma
```tsx
// ✅ Import d'assets Figma (si disponibles)
import svgPaths from "./imports/svg-wg56ef214f";
import imgA from "figma:asset/76faf8f617b56e6f079c5a7ead8f927f5a5fee32.png";
import imgB from "figma:asset/f2dddff10fce8c5cc0468d3c13d16d6eeadcbdb7.png";

// ✅ Utilisation des SVG importés
<div dangerouslySetInnerHTML={{ __html: svgPaths }} />
```

### 5.4 Icônes avec Lucide React
```tsx
// ✅ Import et utilisation des icônes
import { Home, User, Settings, ChevronRight } from 'lucide-react';

// ✅ Icônes en noir uniquement
<Home className="w-5 h-5 text-foreground" />
<User className="w-4 h-4 text-muted-foreground" />

// ❌ INTERDIT - Icônes colorées
<Home className="w-5 h-5 text-blue-500" />
```

## 6. Librairies et versions spécifiques

### 6.1 Versions obligatoires
```tsx
// ✅ Versions spécifiques requises
import { useForm } from 'react-hook-form@7.55.0';
import { toast } from "sonner@2.0.3";

// ✅ Imports sans version (dernière version)
import { motion } from 'motion/react';
import { Icon } from 'lucide-react';
import { ResponsiveContainer, LineChart } from 'recharts';
```

### 6.2 Librairies recommandées
```tsx
// Animation
import { motion } from 'motion/react';  // Toujours appeler "Motion", pas "Framer Motion"

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

### 6.3 Librairies interdites
```tsx
// ❌ INTERDIT
import { motion } from 'framer-motion';     // Utiliser motion/react
import { Resizable } from 'react-resizable'; // Utiliser re-resizable
import Konva from 'konva';                   // Utiliser canvas directement
```

## 7. Structure de fichiers et architecture

### 7.1 Point d'entrée obligatoire
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

// ✅ Export par défaut obligatoire
export default App;
```

### 7.2 Structure des composants
```bash
# ✅ Structure recommandée
/App.tsx                    # Point d'entrée principal
/components/                # Composants personnalisés uniquement
├── header.tsx             # Composants métier
├── sidebar.tsx
├── time-block.tsx
└── ui/                    # ❌ RÉSERVÉ aux composants ShadCN
    ├── button.tsx         # NE PAS MODIFIER
    └── card.tsx           # NE PAS MODIFIER

/components/figma/          # ❌ FICHIERS PROTÉGÉS
└── ImageWithFallback.tsx  # NE PAS MODIFIER

/styles/
└── globals.css            # ❌ NE PAS MODIFIER (sauf tokens)
```

### 7.3 Conventions de nommage
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

### 7.4 Fichiers protégés (NE PAS MODIFIER)
```bash
# ❌ FICHIERS SYSTÈME PROTÉGÉS
/components/figma/ImageWithFallback.tsx
/styles/globals.css                      # Sauf modification de tokens
/components/ui/                          # Tous les fichiers ShadCN
├── button.tsx
├── card.tsx
├── input.tsx
└── ... (tous les composants ShadCN)
```

## 8. Développement et bonnes pratiques

### 8.1 Approche composant-first
```tsx
// ✅ Préférer plusieurs composants
// App.tsx
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

// ❌ Éviter les composants monolithiques
export default function App() {
  return (
    <div className="min-h-screen">
      {/* 500 lignes de JSX dans un seul composant */}
    </div>
  );
}
```

### 8.2 Gestion des états
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

### 8.3 Gestion des listes et keys
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
  <TimeBlock key={index} {...block} />  // ❌ Index comme key
))}
```

### 8.4 Gestion des formulaires
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

## 9. Animations et interactions

### 9.1 Animations avec Motion
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

### 9.2 Transitions CSS
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

### 9.3 États de chargement
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

## 10. Responsive Design et accessibilité

### 10.1 Design responsive
```tsx
// ✅ Classes responsive
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Grille responsive */}
</div>

// ✅ Espacement responsive
<div className="p-4 md:p-6 lg:p-8">
  {/* Padding responsive */}
</div>

// ✅ Typographie responsive (si nécessaire)
<h1 className="text-xl md:text-2xl lg:text-3xl">
  {/* Seulement si explicitement demandé */}
</h1>
```

### 10.2 Accessibilité
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

### 10.3 Sémantique HTML
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

## 11. Gestion des erreurs et feedback

### 11.1 Notifications toast
```tsx
// ✅ Toast avec Sonner
import { toast } from "sonner@2.0.3";

function handleSave() {
  try {
    // Logique de sauvegarde
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

### 11.2 Gestion des erreurs
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
  
  return (
    <div>
      {/* Contenu normal */}
    </div>
  );
}
```

### 11.3 Validation de formulaires
```tsx
// ✅ Validation avec messages d'erreur
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const schema = z.object({
  title: z.string().min(1, 'Le titre est requis'),
  duration: z.number().min(1, 'La durée doit être positive')
});

function CreateForm() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema)
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
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
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

## 12. Performance et optimisation

### 12.1 Lazy loading des composants
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

### 12.2 Mémorisation avec useMemo et useCallback
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

### 12.3 Optimisation des images
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
      loading="lazy"  // Lazy loading natif
    />
  );
}
```

## 13. Tests et qualité du code

### 13.1 Types TypeScript stricts
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

### 13.2 Gestion des cas d'erreur
```tsx
// ✅ Gestion défensive
function TimeBlockCard({ timeBlock, onEdit, onDelete }: TimeBlockCardProps) {
  if (!timeBlock) {
    return null;  // Ou un composant d'erreur
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

### 13.3 Documentation des composants
```tsx
/**
 * Composant de carte pour afficher un bloc de temps
 * 
 * @param timeBlock - Les données du bloc de temps
 * @param onEdit - Callback appelé lors de l'édition
 * @param onDelete - Callback appelé lors de la suppression
 * @param className - Classes CSS additionnelles
 */
function TimeBlockCard({ 
  timeBlock, 
  onEdit, 
  onDelete, 
  className 
}: TimeBlockCardProps) {
  // Implémentation
}
```

## 14. Common Mistakes to Avoid

### 14.1 Erreurs de couleurs
```tsx
// ❌ DON'T: Couleurs hardcodées
<div className="bg-white text-black border-gray-200">
  Contenu
</div>

// ❌ DON'T: Couleurs non-grayscale
<div className="bg-blue-500 text-white">
  Bouton bleu
</div>

// ❌ DON'T: Styles inline avec couleurs
<div style={{ backgroundColor: '#ffffff', color: '#000000' }}>
  Contenu
</div>

// ✅ DO: Tokens sémantiques
<div className="bg-card text-foreground border-border">
  Contenu
</div>

// ✅ DO: Variantes grayscale uniquement
<div className="bg-primary text-primary-foreground">
  Bouton noir
</div>
```

### 14.2 Erreurs de typographie
```tsx
// ❌ DON'T: Classes de typographie
<h1 className="text-3xl font-bold">Titre</h1>
<p className="text-sm text-gray-600">Texte</p>

// ❌ DON'T: Override des styles par défaut
<button className="font-light text-lg">Bouton</button>

// ✅ DO: Utiliser la typographie par défaut
<h1>Titre</h1>  {/* Utilise text-2xl font-medium de globals.css */}
<p className="text-muted-foreground">Texte</p>  {/* Couleur sémantique */}

// ✅ DO: Seulement si explicitement demandé
<h1 className="text-4xl">Titre spécial</h1>  {/* Si demandé par l'utilisateur */}
```

### 14.3 Erreurs de structure
```tsx
// ❌ DON'T: Créer des composants ShadCN personnalisés
// /components/ui/custom-button.tsx
export function CustomButton() { ... }

// ❌ DON'T: Modifier les composants ShadCN existants
// /components/ui/button.tsx - NE PAS MODIFIER

// ❌ DON'T: Import incorrect
import { Button } from '@/components/ui/button';

// ✅ DO: Utiliser les composants ShadCN existants
import { Button } from './components/ui/button';

// ✅ DO: Créer des composants personnalisés ailleurs
// /components/time-block-button.tsx
import { Button } from './ui/button';
export function TimeBlockButton() {
  return <Button className="w-full">...</Button>;
}
```

### 14.4 Erreurs d'images
```tsx
// ❌ DON'T: Balise img directe
<img src="/avatar.jpg" alt="Avatar" />

// ❌ DON'T: Modifier ImageWithFallback
// /components/figma/ImageWithFallback.tsx - FICHIER PROTÉGÉ

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

### 14.5 Erreurs de librairies
```tsx
// ❌ DON'T: Anciennes librairies
import { motion } from 'framer-motion';
import { Resizable } from 'react-resizable';

// ❌ DON'T: Versions incorrectes
import { useForm } from 'react-hook-form';  // Manque @7.55.0
import { toast } from 'sonner';             // Manque @2.0.3

// ✅ DO: Librairies et versions correctes
import { motion } from 'motion/react';
import { Resizable } from 're-resizable';
import { useForm } from 'react-hook-form@7.55.0';
import { toast } from 'sonner@2.0.3';
```

### 14.6 Erreurs de développement
```tsx
// ❌ DON'T: Placeholders dans le code
function Component() {
  return (
    <div>
      <h1>Titre</h1>
      {/* TODO: Ajouter le contenu */}
      {/* Rest of the code remains the same */}
    </div>
  );
}

// ❌ DON'T: Keys non-uniques
{items.map((item, index) => (
  <div key={index}>{item.name}</div>  // Index comme key
))}

// ✅ DO: Implémentation complète
function Component() {
  return (
    <div className="p-6 bg-card">
      <h1>Titre</h1>
      <p className="text-muted-foreground">Contenu complet</p>
    </div>
  );
}

// ✅ DO: Keys uniques
{items.map((item) => (
  <div key={item.id}>{item.name}</div>  // ID unique comme key
))}
```

### 14.7 Erreurs de responsive
```tsx
// ❌ DON'T: Design non-responsive
<div className="w-800 h-600">  // Largeur fixe
  Contenu
</div>

// ❌ DON'T: Breakpoints incorrects
<div className="sm:text-xs md:text-sm lg:text-base">  // Override typographie

// ✅ DO: Design responsive
<div className="w-full max-w-4xl mx-auto">
  Contenu responsive
</div>

// ✅ DO: Breakpoints pour layout uniquement
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  Grille responsive
</div>
```

### 14.8 Erreurs d'accessibilité
```tsx
// ❌ DON'T: Manque d'accessibilité
<div onClick={handleClick}>Bouton</div>  // Pas accessible au clavier
<input />  // Pas de label

// ❌ DON'T: Contraste insuffisant
<span className="text-muted-foreground/30">Texte illisible</span>

// ✅ DO: Accessibilité complète
<Button onClick={handleClick}>Bouton accessible</Button>
<Label htmlFor="input">Label</Label>
<Input id="input" />

// ✅ DO: Contraste suffisant
<span className="text-muted-foreground">Texte lisible</span>
```

## 15. Prompt système pour l'agent de codage frontend

### 15.1 Prompt complet
```
Tu es l'agent de codage frontend pour le projet AGI Time Blocking. Tu DOIS respecter strictement la structure Figma Make existante et le système de design noir/gris/blanc.

RÈGLES ABSOLUES - AUCUNE EXCEPTION:

1. COULEURS STRICTES:
   - Utilise UNIQUEMENT les tokens sémantiques: bg-background, bg-card, bg-muted, bg-accent, bg-primary
   - Texte: text-foreground, text-muted-foreground, text-primary-foreground
   - Bordures: border-border, border-input
   - INTERDIT: bg-white, bg-black, bg-gray-*, text-blue-*, border-red-*, couleurs hex

2. COMPOSANTS SHADCN/UI:
   - Utilise UNIQUEMENT les 47 composants existants dans /components/ui/
   - Import: import { Component } from './components/ui/component'
   - JAMAIS créer de composants dans /components/ui/
   - JAMAIS modifier les composants ShadCN existants

3. STRUCTURE OBLIGATOIRE:
   - App.tsx est le point d'entrée avec export default
   - Composants personnalisés dans /components/ uniquement
   - JAMAIS modifier /components/ui/ ou /styles/globals.css
   - JAMAIS modifier /components/figma/ImageWithFallback.tsx

4. TYPOGRAPHIE:
   - INTERDIT: text-xl, font-bold, leading-none (sauf demande explicite)
   - Utilise la typographie par défaut de globals.css
   - h1, h2, h3, p, button ont des styles prédéfinis

5. IMAGES:
   - Utilise ImageWithFallback pour les nouvelles images
   - Import: import { ImageWithFallback } from './components/figma/ImageWithFallback'
   - JAMAIS utiliser <img> directement

6. LIBRAIRIES:
   - Versions spécifiques: react-hook-form@7.55.0, sonner@2.0.3
   - Motion: import { motion } from 'motion/react'
   - Icônes: import { Icon } from 'lucide-react'

7. DÉVELOPPEMENT:
   - JAMAIS de placeholders (// TODO, // Rest of code)
   - Keys uniques pour les listes (pas d'index)
   - TypeScript strict avec interfaces
   - Gestion d'erreurs complète

AVANT CHAQUE MODIFICATION:
1. Vérifie si un composant ShadCN existe déjà
2. Utilise les tokens sémantiques pour les couleurs
3. Respecte la structure de fichiers existante
4. Évite toute duplication de composants
5. Maintiens la cohérence du design system

EXEMPLES CORRECTS:
✅ <div className="bg-card text-foreground border-border">
✅ import { Button } from './components/ui/button'
✅ <ImageWithFallback src="..." alt="..." width={40} height={40} />
✅ <h1>Titre</h1> // Utilise les styles par défaut

EXEMPLES INTERDITS:
❌ <div className="bg-white text-black border-gray-200">
❌ import { Button } from '@/components/ui/button'
❌ <img src="..." alt="..." />
❌ <h1 className="text-3xl font-bold">Titre</h1>

En cas de doute, DEMANDE confirmation avant de modifier la structure existante.
```

### 15.2 Checklist de validation
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

## 16. Exemples d'implémentation complète

### 16.1 Composant de carte de temps
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
  id,
  title,
  duration,
  startTime,
  isCompleted,
  category,
  onEdit,
  onDelete
}: TimeBlockCardProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getCategoryLabel = (cat: string) => {
    const labels = {
      work: 'Travail',
      personal: 'Personnel',
      break: 'Pause'
    };
    return labels[cat] || cat;
  };

  return (
    <Card className={`transition-colors duration-200 ${
      isCompleted ? 'bg-muted' : 'bg-card'
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className={`text-base ${
            isCompleted ? 'text-muted-foreground line-through' : 'text-foreground'
          }`}>
            {title}
          </CardTitle>
          <Badge variant="secondary" className="ml-2">
            {getCategoryLabel(category)}
          </Badge>
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
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(id)}
                className="h-8 w-8 p-0"
              >
                <Edit className="w-4 h-4" />
              </Button>
            )}
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(id)}
                className="h-8 w-8 p-0 hover:bg-destructive hover:text-destructive-foreground"
              >
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

### 16.2 Formulaire de création
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
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      category: 'work'
    }
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
            <Input
              id="title"
              {...register('title')}
              placeholder="Ex: Réunion équipe"
            />
            {errors.title && (
              <span className="text-destructive text-sm">
                {errors.title.message}
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="duration">Durée (minutes)</Label>
              <Input
                id="duration"
                type="number"
                {...register('duration', { valueAsNumber: true })}
                placeholder="60"
              />
              {errors.duration && (
                <span className="text-destructive text-sm">
                  {errors.duration.message}
                </span>
              )}
            </div>

            <div>
              <Label htmlFor="startTime">Heure de début</Label>
              <Input
                id="startTime"
                type="time"
                {...register('startTime')}
              />
              {errors.startTime && (
                <span className="text-destructive text-sm">
                  {errors.startTime.message}
                </span>
              )}
            </div>
          </div>

          <div>
            <Label>Catégorie</Label>
            <Select
              value={watch('category')}
              onValueChange={(value) => setValue('category', value as any)}
            >
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
            {onCancel && (
              <Button type="button" variant="outline" onClick={onCancel}>
                Annuler
              </Button>
            )}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Création...' : 'Créer'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
```

### 16.3 Layout principal avec sidebar
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
                  <SidebarMenuButton
                    onClick={() => setActiveView(item.id)}
                    className={activeView === item.id ? 'bg-accent' : ''}
                  >
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
                <Button variant="outline" size="sm">
                  Synchroniser
                </Button>
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau
                </Button>
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

---

## 17. PROMPT SYSTÈME COMPLET POUR L'AGENT FRONTEND

### 17.1 Contexte et rôle

```markdown
# AGENT FRONTEND - SPÉCIALISTE REACT/TYPESCRIPT

Tu es l'agent frontend spécialisé dans le développement React/TypeScript pour le projet AGI Time Blocking.

## CONTEXTE PROJET
- Application de gestion du temps avec IA
- Stack: React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui
- Architecture: Clean Architecture avec séparation domaine/infrastructure
- Design system: Basé sur les maquettes Figma fournies

## TON RÔLE
- Développer UNIQUEMENT le frontend React
- Implémenter les designs Figma avec précision pixel-perfect
- Maintenir la cohérence du design system
- Optimiser les performances et l'accessibilité
- Gérer l'état avec Zustand et les requêtes avec TanStack Query

## CONTRAINTES STRICTES
- JAMAIS toucher au backend (Python/GraphQL)
- TOUJOURS utiliser les composants shadcn/ui existants
- RESPECTER l'architecture Clean Architecture
- SUIVRE les conventions TypeScript strictes
- IMPLÉMENTER les designs Figma exactement
```

### 17.2 Architecture et structure

```markdown
## ARCHITECTURE FRONTEND

### Structure des dossiers
```
src/
├── components/          # Composants réutilisables
│   ├── ui/             # shadcn/ui components
│   ├── forms/          # Formulaires spécialisés
│   ├── layout/         # Composants de mise en page
│   └── features/       # Composants métier
├── hooks/              # Custom hooks
├── services/           # Services (API, storage)
├── types/              # Types TypeScript
├── lib/                # Utilitaires
├── config/             # Configuration
└── styles/             # Styles globaux
```

### Conventions de nommage
- Composants: PascalCase (ex: `TimeBlockCard`)
- Hooks: camelCase avec préfixe `use` (ex: `useTimeBlocks`)
- Types: PascalCase avec suffixe `Type` (ex: `TimeBlockType`)
- Services: camelCase avec suffixe `Service` (ex: `apiService`)

### Patterns obligatoires
- Composition over inheritance
- Custom hooks pour la logique métier
- Props interfaces explicites
- Error boundaries pour la gestion d'erreurs
- Lazy loading pour les routes
```

### 17.3 Standards de développement

```markdown
## STANDARDS DE QUALITÉ

### TypeScript
- Mode strict activé
- Pas de `any` autorisé
- Interfaces explicites pour tous les props
- Types utilitaires (Pick, Omit, Partial) encouragés
- Génériques pour la réutilisabilité

### React
- Functional components uniquement
- Hooks personnalisés pour la logique complexe
- Memoization avec React.memo, useMemo, useCallback
- Gestion d'état locale avec useState/useReducer
- Gestion d'état globale avec Zustand

### Performance
- Code splitting par route
- Lazy loading des composants lourds
- Optimisation des re-renders
- Debouncing pour les inputs
- Virtualisation pour les longues listes

### Accessibilité
- Attributs ARIA appropriés
- Navigation au clavier
- Contraste suffisant
- Labels explicites
- Focus management
```

### 17.4 Intégration API

```markdown
## INTÉGRATION GRAPHQL

### Configuration Apollo Client
```typescript
// src/config/apollo.ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: import.meta.env.VITE_GRAPHQL_ENDPOINT || 'http://localhost:8000/graphql',
});

const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('auth-token');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  };
});

export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});
```

### Hooks personnalisés pour les requêtes
```typescript
// src/hooks/useTimeBlocks.ts
import { useQuery, useMutation } from '@apollo/client';
import { GET_TIME_BLOCKS, CREATE_TIME_BLOCK } from '../graphql/queries';

export function useTimeBlocks() {
  const { data, loading, error, refetch } = useQuery(GET_TIME_BLOCKS);
  
  const [createTimeBlock] = useMutation(CREATE_TIME_BLOCK, {
    refetchQueries: [GET_TIME_BLOCKS],
  });

  return {
    timeBlocks: data?.timeBlocks || [],
    loading,
    error,
    refetch,
    createTimeBlock,
  };
}
```
```

### 17.5 Gestion d'état

```markdown
## ZUSTAND STORE ARCHITECTURE

### Store principal
```typescript
// src/stores/appStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppState {
  // UI State
  sidebarOpen: boolean;
  currentView: 'calendar' | 'timeblocks' | 'settings';
  theme: 'light' | 'dark' | 'system';
  
  // User State
  user: User | null;
  isAuthenticated: boolean;
  
  // Actions
  setSidebarOpen: (open: boolean) => void;
  setCurrentView: (view: string) => void;
  setTheme: (theme: string) => void;
  setUser: (user: User | null) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      sidebarOpen: true,
      currentView: 'calendar',
      theme: 'system',
      user: null,
      isAuthenticated: false,
      
      // Actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setCurrentView: (view) => set({ currentView: view }),
      setTheme: (theme) => set({ theme }),
      setUser: (user) => set({ 
        user, 
        isAuthenticated: !!user 
      }),
    }),
    { name: 'app-store' }
  )
);
```

### Store spécialisés
```typescript
// src/stores/timeBlockStore.ts
import { create } from 'zustand';
import { TimeBlock } from '../types';

interface TimeBlockState {
  selectedDate: Date;
  selectedTimeBlock: TimeBlock | null;
  isCreating: boolean;
  
  setSelectedDate: (date: Date) => void;
  setSelectedTimeBlock: (timeBlock: TimeBlock | null) => void;
  setIsCreating: (creating: boolean) => void;
}

export const useTimeBlockStore = create<TimeBlockState>((set) => ({
  selectedDate: new Date(),
  selectedTimeBlock: null,
  isCreating: false,
  
  setSelectedDate: (date) => set({ selectedDate: date }),
  setSelectedTimeBlock: (timeBlock) => set({ selectedTimeBlock: timeBlock }),
  setIsCreating: (creating) => set({ isCreating: creating }),
}));
```
```

---

## 18. CHECKLIST DE VALIDATION

### 18.1 Checklist développement

```markdown
## ✅ CHECKLIST AVANT COMMIT

### Code Quality
- [ ] Pas d'erreurs TypeScript
- [ ] Pas de console.log oubliés
- [ ] Pas de TODO/FIXME non documentés
- [ ] Imports organisés et optimisés
- [ ] Composants documentés avec JSDoc
- [ ] Props interfaces définies
- [ ] Gestion d'erreur implémentée

### Performance
- [ ] Composants memoizés si nécessaire
- [ ] Hooks optimisés (useCallback, useMemo)
- [ ] Pas de re-renders inutiles
- [ ] Images optimisées
- [ ] Code splitting appliqué
- [ ] Bundle size vérifié

### Accessibilité
- [ ] Navigation clavier fonctionnelle
- [ ] Attributs ARIA présents
- [ ] Contraste suffisant
- [ ] Labels explicites
- [ ] Focus visible
- [ ] Screen reader compatible

### Design System
- [ ] Composants shadcn/ui utilisés
- [ ] Tokens de design respectés
- [ ] Responsive design implémenté
- [ ] Dark mode supporté
- [ ] Animations fluides
- [ ] Cohérence visuelle
```

### 18.2 Tests et validation

```markdown
## 🧪 TESTS OBLIGATOIRES

### Tests unitaires
```typescript
// src/components/__tests__/TimeBlockCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TimeBlockCard } from '../TimeBlockCard';

describe('TimeBlockCard', () => {
  const mockTimeBlock = {
    id: '1',
    title: 'Test Block',
    startTime: '09:00',
    duration: 60,
    category: 'work'
  };

  it('renders time block information', () => {
    render(<TimeBlockCard timeBlock={mockTimeBlock} />);
    
    expect(screen.getByText('Test Block')).toBeInTheDocument();
    expect(screen.getByText('09:00')).toBeInTheDocument();
    expect(screen.getByText('60 min')).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<TimeBlockCard timeBlock={mockTimeBlock} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith(mockTimeBlock);
  });
});
```

### Tests d'intégration
```typescript
// src/pages/__tests__/CalendarPage.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MockedProvider } from '@apollo/client/testing';
import { CalendarPage } from '../CalendarPage';
import { GET_TIME_BLOCKS } from '../../graphql/queries';

const mocks = [
  {
    request: { query: GET_TIME_BLOCKS },
    result: {
      data: {
        timeBlocks: [
          { id: '1', title: 'Meeting', startTime: '09:00', duration: 60 }
        ]
      }
    }
  }
];

describe('CalendarPage', () => {
  it('displays time blocks from API', async () => {
    render(
      <MockedProvider mocks={mocks}>
        <CalendarPage />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Meeting')).toBeInTheDocument();
    });
  });
});
```
```

### 18.3 Validation design

```markdown
## 🎨 VALIDATION DESIGN FIGMA

### Checklist pixel-perfect
- [ ] Espacements respectés (padding, margin)
- [ ] Typographie conforme (font-size, line-height, font-weight)
- [ ] Couleurs exactes (tokens de couleur)
- [ ] Bordures et radius corrects
- [ ] Ombres et effets appliqués
- [ ] États interactifs (hover, focus, active)
- [ ] Animations et transitions

### Responsive design
- [ ] Mobile (320px-768px) ✓
- [ ] Tablet (768px-1024px) ✓
- [ ] Desktop (1024px+) ✓
- [ ] Breakpoints intermédiaires ✓
- [ ] Navigation adaptative ✓
- [ ] Contenu réorganisé ✓

### Dark mode
- [ ] Couleurs adaptées
- [ ] Contraste maintenu
- [ ] Images/icônes ajustées
- [ ] Transitions fluides
- [ ] Préférence système respectée
```

---

## 19. TROUBLESHOOTING COURANT

### 19.1 Problèmes fréquents

```markdown
## 🔧 PROBLÈMES COURANTS ET SOLUTIONS

### Erreurs TypeScript
**Problème:** `Property 'X' does not exist on type 'Y'`
```typescript
// ❌ Mauvais
const user = data.user; // data peut être undefined

// ✅ Correct
const user = data?.user;
// ou
if (data && data.user) {
  const user = data.user;
}
```

**Problème:** `Type 'string | undefined' is not assignable to type 'string'`
```typescript
// ❌ Mauvais
const id: string = props.id; // props.id peut être undefined

// ✅ Correct
const id = props.id || '';
// ou
const id = props.id ?? 'default-id';
```

### Erreurs React
**Problème:** Re-renders infinis
```typescript
// ❌ Mauvais - crée un nouvel objet à chaque render
const config = { option: true };

// ✅ Correct - memoize l'objet
const config = useMemo(() => ({ option: true }), []);
```

**Problème:** État non mis à jour
```typescript
// ❌ Mauvais - mutation directe
const updateItem = (id: string) => {
  const item = items.find(i => i.id === id);
  item.status = 'updated'; // Mutation!
  setItems(items);
};

// ✅ Correct - immutabilité
const updateItem = (id: string) => {
  setItems(items.map(item => 
    item.id === id 
      ? { ...item, status: 'updated' }
      : item
  ));
};
```
```

### 19.2 Performance

```markdown
## ⚡ OPTIMISATION PERFORMANCE

### Lazy loading
```typescript
// Lazy loading des pages
const CalendarPage = lazy(() => import('./pages/CalendarPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

// Dans le router
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/calendar" element={<CalendarPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Routes>
</Suspense>
```

### Memoization
```typescript
// Memoize les composants coûteux
const ExpensiveComponent = React.memo(({ data, onUpdate }) => {
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      computed: heavyComputation(item)
    }));
  }, [data]);

  const handleUpdate = useCallback((id: string) => {
    onUpdate(id);
  }, [onUpdate]);

  return (
    <div>
      {processedData.map(item => (
        <Item key={item.id} data={item} onUpdate={handleUpdate} />
      ))}
    </div>
  );
});
```

### Bundle optimization
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-select'],
          utils: ['date-fns', 'lodash-es']
        }
      }
    }
  }
});
```
```

### 19.3 Debugging

```markdown
## 🐛 DEBUGGING TECHNIQUES

### React DevTools
- Utiliser React DevTools pour inspecter les composants
- Profiler pour identifier les re-renders
- Vérifier les props et l'état

### Console debugging
```typescript
// Debug conditionnel
const DEBUG = import.meta.env.DEV;

const MyComponent = ({ data }) => {
  if (DEBUG) {
    console.log('MyComponent render:', { data });
  }
  
  // Utiliser useEffect pour tracker les changements
  useEffect(() => {
    if (DEBUG) {
      console.log('Data changed:', data);
    }
  }, [data]);
  
  return <div>{/* component */}</div>;
};
```

### Error boundaries
```typescript
// src/components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Envoyer à un service de monitoring
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Quelque chose s'est mal passé</h2>
          <button onClick={() => this.setState({ hasError: false })}>
            Réessayer
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```
```

---

## 20. CONCLUSION ET NEXT STEPS

### 20.1 Récapitulatif

Ce document fournit une base complète pour l'intégration frontend du projet AGI Time Blocking. Il couvre :

- **Architecture React moderne** avec TypeScript et Clean Architecture
- **Design system cohérent** basé sur shadcn/ui et les maquettes Figma
- **Composants réutilisables** pour toutes les fonctionnalités principales
- **Gestion d'état optimisée** avec Zustand et TanStack Query
- **Standards de qualité** avec tests, accessibilité et performance
- **Documentation complète** pour les développeurs

### 20.2 Prochaines étapes

1. **Phase 1 - Setup initial** (1-2 jours)
   - Configuration du projet Vite + TypeScript
   - Installation et configuration de shadcn/ui
   - Setup des stores Zustand
   - Configuration Apollo Client

2. **Phase 2 - Composants de base** (3-5 jours)
   - Implémentation des composants UI de base
   - Layout principal avec sidebar
   - Système de navigation
   - Thème et dark mode

3. **Phase 3 - Fonctionnalités principales** (1-2 semaines)
   - Calendrier et vue timeline
   - Gestion des time blocks
   - Formulaires de création/édition
   - Intégration API GraphQL

4. **Phase 4 - Optimisation** (3-5 jours)
   - Tests unitaires et d'intégration
   - Optimisation des performances
   - Validation accessibilité
   - Documentation finale

### 20.3 Ressources utiles

- **Documentation officielle:** [React](https://react.dev), [TypeScript](https://typescriptlang.org), [Vite](https://vitejs.dev)
- **Design system:** [shadcn/ui](https://ui.shadcn.com), [Radix UI](https://radix-ui.com)
- **État et requêtes:** [Zustand](https://zustand-demo.pmnd.rs), [TanStack Query](https://tanstack.com/query)
- **Tests:** [Vitest](https://vitest.dev), [Testing Library](https://testing-library.com)
- **Outils:** [React DevTools](https://react.dev/learn/react-developer-tools), [TypeScript Playground](https://typescriptlang.org/play)

---

**Document complet - Version finale**
**Dernière mise à jour:** 22 octobre 2025
**Lignes totales:** 2,247