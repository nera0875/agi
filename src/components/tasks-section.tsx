import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export function TasksSection() {
  return (
    <div className="space-y-6">
      <div>
        <h2>Tasks Service</h2>
        <p className="text-muted-foreground">
          Les mutations et requêtes Tasks ne sont pas encore disponibles sur le
          backend AGI. Cette section reste en lecture seule pour le moment.
        </p>
      </div>

      <Card className="border-dashed border-muted-foreground/50">
        <CardContent className="py-10 text-center text-sm text-muted-foreground space-y-2">
          <p>• Création et suivi des tâches</p>
          <p>• Sessions Pomodoro synchronisées</p>
          <p>• Statistiques de productivité</p>
          <p className="text-foreground">à venir</p>
        </CardContent>
      </Card>
    </div>
  );
}
