import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "./ui/sheet";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Slider } from "./ui/slider";
import { X, Plus, Target } from "lucide-react";
import { toast } from "sonner";

type NewTaskSheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const priorityOptions = [
  { value: "low", label: "Basse", color: "bg-chart-2" },
  { value: "medium", label: "Moyenne", color: "bg-chart-4" },
  { value: "high", label: "Haute", color: "bg-destructive" },
];

const statusOptions = [
  { value: "pending", label: "En attente" },
  { value: "in-progress", label: "En cours" },
  { value: "completed", label: "Terminée" },
];

export function NewTaskSheet({ open, onOpenChange }: NewTaskSheetProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [status, setStatus] = useState("pending");
  const [estimatedPomodoros, setEstimatedPomodoros] = useState([4]);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");

  const handleAddTag = (tag: string) => {
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleSubmit = () => {
    if (!title.trim()) {
      toast.error("Le titre de la tâche est requis");
      return;
    }

    // TODO: Call GraphQL mutation
    toast.success("Tâche créée avec succès", {
      description: `Priorité: ${priority}, Pomodoros: ${estimatedPomodoros[0]}`,
    });

    // Reset form
    setTitle("");
    setDescription("");
    setPriority("medium");
    setStatus("pending");
    setEstimatedPomodoros([4]);
    setTags([]);
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-chart-4" />
            Nouvelle Tâche
          </SheetTitle>
          <SheetDescription>
            Créez une nouvelle tâche et planifiez son exécution
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 py-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="task-title">Titre *</Label>
            <Input
              id="task-title"
              placeholder="Ex: Implémenter l'authentification GraphQL"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="task-description">Description</Label>
            <Textarea
              id="task-description"
              placeholder="Décrivez la tâche en détail..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Priority & Status */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="task-priority">Priorité</Label>
              <Select value={priority} onValueChange={setPriority}>
                <SelectTrigger id="task-priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {priorityOptions.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      <div className="flex items-center gap-2">
                        <div className={`h-2 w-2 rounded-full ${p.color}`} />
                        {p.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="task-status">Statut</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger id="task-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Estimated Pomodoros */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Pomodoros estimés</Label>
              <Badge variant="secondary">{estimatedPomodoros[0]}</Badge>
            </div>
            <Slider
              value={estimatedPomodoros}
              onValueChange={setEstimatedPomodoros}
              min={1}
              max={16}
              step={1}
            />
            <p className="text-xs text-muted-foreground">
              Environ {estimatedPomodoros[0] * 25} minutes de travail
            </p>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label>Tags</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Ajouter un tag..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag(newTag);
                  }
                }}
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => handleAddTag(newTag)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1">
                    {tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Quick Tags */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Tags rapides :</p>
            <div className="flex flex-wrap gap-2">
              {["Urgent", "Bug", "Feature", "Refactor", "Documentation"].map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="cursor-pointer hover:bg-accent"
                  onClick={() => handleAddTag(tag)}
                >
                  + {tag}
                </Badge>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => onOpenChange(false)}
            >
              Annuler
            </Button>
            <Button
              className="flex-1"
              onClick={handleSubmit}
              disabled={!title.trim()}
            >
              Créer la tâche
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
