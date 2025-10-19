import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import {
  Brain,
  CheckCircle,
  Database,
  FileText,
  Clock,
  TrendingUp,
} from "lucide-react";

interface Activity {
  id: string;
  type: "memory" | "task" | "database" | "file" | "pomodoro";
  title: string;
  description: string;
  timestamp: Date;
  status?: "completed" | "in_progress" | "pending";
}

const mockActivities: Activity[] = [
  {
    id: "1",
    type: "memory",
    title: "Nouvelle mémoire créée",
    description: "React best practices pour hooks",
    timestamp: new Date(Date.now() - 5 * 60000),
    status: "completed",
  },
  {
    id: "2",
    type: "task",
    title: "Tâche complétée",
    description: "Intégrer l'API GraphQL",
    timestamp: new Date(Date.now() - 15 * 60000),
    status: "completed",
  },
  {
    id: "3",
    type: "database",
    title: "Données synchronisées",
    description: "Neo4j sync - 127 nodes mis à jour",
    timestamp: new Date(Date.now() - 30 * 60000),
  },
  {
    id: "4",
    type: "pomodoro",
    title: "Session terminée",
    description: "25min - Focus sur développement",
    timestamp: new Date(Date.now() - 45 * 60000),
    status: "completed",
  },
  {
    id: "5",
    type: "file",
    title: "Fichier modifié",
    description: "brain-section.tsx",
    timestamp: new Date(Date.now() - 60 * 60000),
  },
];

export function RecentActivity() {
  const getIcon = (type: string) => {
    switch (type) {
      case "memory":
        return <Brain className="h-4 w-4 text-chart-1" />;
      case "task":
        return <CheckCircle className="h-4 w-4 text-chart-2" />;
      case "database":
        return <Database className="h-4 w-4 text-chart-3" />;
      case "file":
        return <FileText className="h-4 w-4 text-chart-4" />;
      case "pomodoro":
        return <Clock className="h-4 w-4 text-chart-5" />;
      default:
        return <TrendingUp className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000 / 60);

    if (diff < 1) return "À l'instant";
    if (diff < 60) return `${diff}min`;
    if (diff < 1440) return `${Math.floor(diff / 60)}h`;
    return `${Math.floor(diff / 1440)}j`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activité récente</CardTitle>
        <CardDescription>Dernières actions système</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="space-y-3">
            {mockActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 rounded-lg border p-3 hover:bg-accent/50 transition-colors"
              >
                <div className="mt-0.5">{getIcon(activity.type)}</div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{activity.title}</p>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(activity.timestamp)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {activity.description}
                  </p>
                  {activity.status && (
                    <Badge variant="outline" className="text-xs">
                      {activity.status === "completed"
                        ? "Complété"
                        : activity.status === "in_progress"
                        ? "En cours"
                        : "En attente"}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
