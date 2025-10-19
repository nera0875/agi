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
import { X, Plus, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useCreateMemory } from "../lib/graphql-hooks";

type NewMemorySheetProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const memoryTypes = [
  { value: "context", label: "Contexte" },
  { value: "preference", label: "Préférence" },
  { value: "knowledge", label: "Connaissance" },
  { value: "instruction", label: "Instruction" },
];

const suggestedTags = [
  "React", "Python", "GraphQL", "API", "UI/UX", "Backend",
  "Frontend", "Database", "DevOps", "Architecture"
];

export function NewMemorySheet({ open, onOpenChange }: NewMemorySheetProps) {
  const [text, setText] = useState("");
  const [type, setType] = useState("context");
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  
  const [createMemory, { loading }] = useCreateMemory({
    onCompleted: (memory) => {
      toast.success("Mémoire créée", {
        description: `ID: ${memory.id}`,
      });
      setText("");
      setType("context");
      setTags([]);
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error("Erreur réseau", {
        description: error.message,
      });
    },
  });

  const handleAddTag = (tag: string) => {
    if (tag && !tags.includes(tag)) {
      setTags([...tags, tag]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleSubmit = async () => {
    if (!text.trim()) {
      toast.error("Le texte de la mémoire est requis");
      return;
    }

    await createMemory({
      content: text,
      sourceType: type,
      metadata: {
        type,
        tags,
        created_at: new Date().toISOString(),
      },
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-chart-1" />
            Nouvelle Mémoire
          </SheetTitle>
          <SheetDescription>
            Créez une nouvelle entrée de mémoire pour enrichir la base de connaissances
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 py-6">
          {/* Memory Text */}
          <div className="space-y-2">
            <Label htmlFor="memory-text">Texte de la mémoire *</Label>
            <Textarea
              id="memory-text"
              placeholder="Ex: L'utilisateur préfère utiliser React avec TypeScript pour les projets frontend..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              className="resize-none"
            />
            <p className="text-xs text-muted-foreground">
              {text.length} caractères
            </p>
          </div>

          {/* Memory Type */}
          <div className="space-y-2">
            <Label htmlFor="memory-type">Type de mémoire</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger id="memory-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {memoryTypes.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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

            {/* Suggested Tags */}
            <div className="space-y-2 pt-2">
              <p className="text-xs text-muted-foreground">Tags suggérés :</p>
              <div className="flex flex-wrap gap-2">
                {suggestedTags
                  .filter(tag => !tags.includes(tag))
                  .slice(0, 6)
                  .map((tag) => (
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
              disabled={!text.trim() || loading}
            >
              {loading ? "Création..." : "Créer la mémoire"}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
