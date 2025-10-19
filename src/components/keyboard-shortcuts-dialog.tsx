import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { Keyboard, Command } from "lucide-react";

type KeyboardShortcutsDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

type Shortcut = {
  keys: string[];
  description: string;
  category: string;
};

const shortcuts: Shortcut[] = [
  // Navigation
  { keys: ["Ctrl", "K"], description: "Ouvrir la palette de commandes", category: "Navigation" },
  { keys: ["G", "O"], description: "Aller à Overview", category: "Navigation" },
  { keys: ["G", "B"], description: "Aller à Brain", category: "Navigation" },
  { keys: ["G", "W"], description: "Aller à Work", category: "Navigation" },
  { keys: ["G", "H"], description: "Aller à Health", category: "Navigation" },
  { keys: ["G", "S"], description: "Aller à System", category: "Navigation" },
  
  // Actions
  { keys: ["N", "M"], description: "Nouvelle mémoire", category: "Actions" },
  { keys: ["N", "T"], description: "Nouvelle tâche", category: "Actions" },
  { keys: ["N", "P"], description: "Démarrer un pomodoro", category: "Actions" },
  { keys: ["Ctrl", "E"], description: "Exporter les données", category: "Actions" },
  
  // Interface
  { keys: ["Ctrl", "B"], description: "Basculer la sidebar", category: "Interface" },
  { keys: ["Ctrl", "T"], description: "Changer le thème", category: "Interface" },
  { keys: ["?"], description: "Afficher les raccourcis", category: "Interface" },
  { keys: ["Esc"], description: "Fermer les modales", category: "Interface" },
];

const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
  if (!acc[shortcut.category]) {
    acc[shortcut.category] = [];
  }
  acc[shortcut.category].push(shortcut);
  return acc;
}, {} as Record<string, Shortcut[]>);

function KeyBadge({ children }: { children: string }) {
  return (
    <Badge variant="outline" className="px-2 py-1 font-mono text-xs">
      {children === "Ctrl" ? (
        <div className="flex items-center gap-1">
          <Command className="h-3 w-3" />
          <span className="hidden sm:inline">Ctrl</span>
        </div>
      ) : (
        children
      )}
    </Badge>
  );
}

export function KeyboardShortcutsDialog({ open, onOpenChange }: KeyboardShortcutsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Raccourcis Clavier
          </DialogTitle>
          <DialogDescription>
            Utilisez ces raccourcis pour naviguer plus rapidement dans le dashboard
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {Object.entries(groupedShortcuts).map(([category, shortcuts]) => (
            <div key={category} className="space-y-3">
              <h4 className="text-sm text-muted-foreground">{category}</h4>
              <div className="space-y-2">
                {shortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent/50 transition-colors"
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <div className="flex items-center gap-1">
                      {shortcut.keys.map((key, i) => (
                        <div key={i} className="flex items-center">
                          <KeyBadge>{key}</KeyBadge>
                          {i < shortcut.keys.length - 1 && (
                            <span className="mx-1 text-xs text-muted-foreground">+</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              {category !== "Interface" && <Separator />}
            </div>
          ))}
        </div>

        <div className="pt-4 border-t">
          <p className="text-xs text-muted-foreground text-center">
            Astuce : Appuyez sur <KeyBadge>?</KeyBadge> à tout moment pour afficher cette aide
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
