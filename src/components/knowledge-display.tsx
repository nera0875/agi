import { useAllKnowledge } from "@/lib/graphql-hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

export function KnowledgeDisplay() {
  const { data: knowledge, loading, error } = useAllKnowledge();

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Erreur lors du chargement des connaissances: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!knowledge || knowledge.length === 0) {
    return (
      <Alert>
        <AlertDescription>Aucune connaissance trouvée</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {knowledge.map((entry) => (
        <div
          key={entry.id}
          className="rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-semibold text-sm text-gray-900">
                {entry.section}
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                Priorité: {entry.priority}
              </p>
            </div>
            <div className="flex gap-2">
              {entry.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          <p className="text-sm text-gray-700 mb-3 line-clamp-3">
            {entry.content}
          </p>

          <div className="flex justify-between text-xs text-gray-500">
            <span>
              Créé: {entry.created_at
                ? format(new Date(entry.created_at), "dd/MM/yyyy HH:mm")
                : "N/A"}
            </span>
            <span>
              Modifié: {entry.updated_at
                ? format(new Date(entry.updated_at), "dd/MM/yyyy HH:mm")
                : "N/A"}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
