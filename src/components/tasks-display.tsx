import { useAllTasks } from "@/lib/graphql-hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle2, Clock, AlertTriangle, XCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

const statusIcons = {
  pending: <Clock className="h-4 w-4 text-gray-400" />,
  running: <Clock className="h-4 w-4 text-blue-500 animate-spin" />,
  success: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
};

const statusColors = {
  pending: "bg-gray-50 border-gray-200",
  running: "bg-blue-50 border-blue-200",
  success: "bg-green-50 border-green-200",
  failed: "bg-red-50 border-red-200",
};

export function TasksDisplay() {
  const { data: tasks, loading, error } = useAllTasks();

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-28 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Erreur lors du chargement des tâches: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!tasks || tasks.length === 0) {
    return (
      <Alert>
        <AlertDescription>Aucune tâche trouvée</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {tasks.map((task) => (
        <div
          key={task.id}
          className={`rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow ${
            statusColors[task.status as keyof typeof statusColors] ||
            "bg-white border-gray-200"
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              {statusIcons[task.status as keyof typeof statusIcons] || (
                <div className="h-4 w-4" />
              )}
              <div>
                <h3 className="font-semibold text-sm text-gray-900">
                  {task.task_type}
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  ID: {task.id}
                </p>
              </div>
            </div>
            <Badge
              variant={
                task.status === "success"
                  ? "default"
                  : task.status === "failed"
                    ? "destructive"
                    : task.status === "running"
                      ? "secondary"
                      : "outline"
              }
            >
              {task.status}
            </Badge>
          </div>

          {task.result && (
            <div className="mb-3 p-3 bg-white/50 rounded border border-gray-100">
              <p className="text-xs font-medium text-gray-600 mb-1">Résultat:</p>
              <p className="text-xs text-gray-700 line-clamp-2">{task.result}</p>
            </div>
          )}

          {task.error_message && (
            <div className="mb-3 p-3 bg-red-50 rounded border border-red-100">
              <p className="text-xs font-medium text-red-600 mb-1">Erreur:</p>
              <p className="text-xs text-red-700 line-clamp-2">
                {task.error_message}
              </p>
            </div>
          )}

          <div className="flex justify-between text-xs text-gray-500">
            <span>Créé: {format(new Date(task.created_at), "dd/MM/yyyy HH:mm")}</span>
            <span>
              Modifié: {format(new Date(task.updated_at), "dd/MM/yyyy HH:mm")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
