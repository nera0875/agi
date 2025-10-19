import { useEffect, useState } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "./ui/command";
import {
  LayoutDashboard,
  Brain,
  Briefcase,
  Zap,
  Server,
  Settings,
  Plus,
  Search,
  FileText,
  CheckSquare,
  Database,
  Terminal,
  Key,
  ScrollText,
  Shield,
  Code2,
  BookOpen,
} from "lucide-react";

type Section = "overview" | "brain" | "work" | "health" | "system" | "settings";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNavigate: (section: Section) => void;
  onNewMemory: () => void;
  onNewTask: () => void;
}

export function CommandPalette({
  open,
  onOpenChange,
  onNavigate,
  onNewMemory,
  onNewTask,
}: CommandPaletteProps) {
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, onOpenChange]);

  const handleNavigate = (section: Section) => {
    onNavigate(section);
    onOpenChange(false);
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Rechercher ou taper une commande..." />
      <CommandList>
        <CommandEmpty>Aucun résultat trouvé.</CommandEmpty>
        
        <CommandGroup heading="Navigation">
          <CommandItem onSelect={() => handleNavigate("overview")}>
            <LayoutDashboard className="mr-2 h-4 w-4" />
            <span>Vue d'ensemble</span>
          </CommandItem>
          <CommandItem onSelect={() => handleNavigate("brain")}>
            <Brain className="mr-2 h-4 w-4" />
            <span>Brain - Mémoire & Base de données</span>
          </CommandItem>
          <CommandItem onSelect={() => handleNavigate("work")}>
            <Briefcase className="mr-2 h-4 w-4" />
            <span>Work - Tâches & Pomodoro</span>
          </CommandItem>
          <CommandItem onSelect={() => handleNavigate("health")}>
            <Zap className="mr-2 h-4 w-4" />
            <span>Health - Monitoring & Logs</span>
          </CommandItem>
          <CommandItem onSelect={() => handleNavigate("system")}>
            <Server className="mr-2 h-4 w-4" />
            <span>System - Infrastructure</span>
          </CommandItem>
          <CommandItem onSelect={() => handleNavigate("settings")}>
            <Settings className="mr-2 h-4 w-4" />
            <span>Paramètres</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Actions rapides">
          <CommandItem
            onSelect={() => {
              onNewMemory();
              onOpenChange(false);
            }}
          >
            <Plus className="mr-2 h-4 w-4" />
            <span>Nouvelle mémoire</span>
            <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-xs text-muted-foreground">
              N M
            </kbd>
          </CommandItem>
          <CommandItem
            onSelect={() => {
              onNewTask();
              onOpenChange(false);
            }}
          >
            <CheckSquare className="mr-2 h-4 w-4" />
            <span>Nouvelle tâche</span>
            <kbd className="ml-auto pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-xs text-muted-foreground">
              N T
            </kbd>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Rechercher dans...">
          <CommandItem>
            <Search className="mr-2 h-4 w-4" />
            <span>Mémoires</span>
          </CommandItem>
          <CommandItem>
            <CheckSquare className="mr-2 h-4 w-4" />
            <span>Tâches</span>
          </CommandItem>
          <CommandItem>
            <Database className="mr-2 h-4 w-4" />
            <span>Base de données</span>
          </CommandItem>
          <CommandItem>
            <FileText className="mr-2 h-4 w-4" />
            <span>Fichiers</span>
          </CommandItem>
          <CommandItem>
            <ScrollText className="mr-2 h-4 w-4" />
            <span>Logs système</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="System">
          <CommandItem>
            <Terminal className="mr-2 h-4 w-4" />
            <span>Ouvrir Terminal</span>
          </CommandItem>
          <CommandItem>
            <Key className="mr-2 h-4 w-4" />
            <span>Gérer les secrets</span>
          </CommandItem>
          <CommandItem>
            <Shield className="mr-2 h-4 w-4" />
            <span>Règles d'automatisation</span>
          </CommandItem>
          <CommandItem>
            <Code2 className="mr-2 h-4 w-4" />
            <span>Serveurs MCP</span>
          </CommandItem>
          <CommandItem>
            <BookOpen className="mr-2 h-4 w-4" />
            <span>Knowledge Base</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
