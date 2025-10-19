import { useAllRoadmap } from "@/lib/graphql-hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle2, Clock, AlertTriangle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

const statusIcons = {
  active: <Clock className="h-4 w-4 text-blue-500" />,
  pending: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  completed: <CheckCircle2 className="h-4 w-4 text-green-500" />,
};

const statusColors = {
  active: "bg-blue-50 border-blue-200",
  pending: "bg-yellow-50 border-yellow-200",
  completed: "bg-green-50 border-green-200",
};

export function RoadmapDisplay() {
  const { data: roadmap, loading, error } = useAllRoadmap();

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Erreur lors du chargement de la feuille de route: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!roadmap || roadmap.length === 0) {
    return (
      <Alert>
        <AlertDescription>Aucun élément de feuille de route trouvé</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {roadmap.map((item) => (
        <div
          key={item.id}
          className={`rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow ${
            statusColors[item.status as keyof typeof statusColors] ||
            "bg-white border-gray-200"
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              {statusIcons[item.status as keyof typeof statusIcons] || (
                <div className="h-4 w-4" />
              )}
              <div>
                <h3 className="font-semibold text-sm text-gray-900">
                  {item.phase}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Priorité: {item.priority}
                </p>
              </div>
            </div>
            <Badge
              variant={
                item.status === "completed"
                  ? "default"
                  : item.status === "active"
                    ? "secondary"
                    : "outline"
              }
            >
              {item.status}
            </Badge>
          </div>

          {item.next_actions.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-600 mb-2">
                Prochaines actions:
              </p>
              <ul className="space-y-1">
                {item.next_actions.map((action, idx) => (
                  <li key={idx} className="text-xs text-gray-700 ml-4">
                    • {action}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex justify-between text-xs text-gray-500">
            <span>Créé: {format(new Date(item.created_at), "dd/MM/yyyy")}</span>
            <span>
              Modifié: {format(new Date(item.updated_at), "dd/MM/yyyy")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
