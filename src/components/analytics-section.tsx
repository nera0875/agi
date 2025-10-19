import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Skeleton } from "./ui/skeleton";
import { useHealthStatuses } from "../lib/graphql-hooks";

export function AnalyticsSection() {
  const { data, loading } = useHealthStatuses();

  return (
    <div className="space-y-6">
      <div>
        <h2>Analytics</h2>
        <p className="text-muted-foreground">
          Les métriques avancées seront activées après la mise en place de la
          télémétrie backend.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Statut des services</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {loading ? (
            <>
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-5 w-36" />
            </>
          ) : (
            data.map((status) => (
              <div
                key={status.service}
                className="flex items-center justify-between rounded border border-muted/40 px-3 py-2"
              >
                <span className="font-medium">{status.service}</span>
                <span
                  className={
                    status.status ? "text-green-500" : "text-destructive"
                  }
                >
                  {status.status ? "OK" : status.message ?? "OFF"}
                </span>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Prochaines étapes</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>
            • Collecte métriques mémoire (pgvector, cache) via Prometheus/StatsD
          </p>
          <p>• Export traces LangSmith pour dashboards dédiés</p>
          <p>• Intégration alerting Sentry et rapports hebdomadaires</p>
        </CardContent>
      </Card>
    </div>
  );
}
