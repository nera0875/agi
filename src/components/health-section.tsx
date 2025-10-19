import { useMemo } from 'react';
import { Activity, RefreshCw, ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { useHealthStatuses } from '../lib/graphql-hooks';
import { toast } from 'sonner';

export function HealthSection() {
  const {
    data: statuses,
    loading,
    error,
    refetch,
  } = useHealthStatuses({ pollIntervalMs: 30_000 });

  const critical = useMemo(
    () => statuses.filter((status) => !status.status),
    [statuses]
  );

  const handleRefresh = async () => {
    try {
      await refetch();
      toast.success('Statut rafraîchi');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erreur inconnue';
      toast.info('Mode démo - Backend déconnecté', {
        description: 'Les données ne peuvent pas être actualisées',
      });
      console.warn('Health check error:', errorMsg);
    }
  };

  // Mode dégradé: backend offline
  if (error && statuses.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2>Health</h2>
            <p className="text-muted-foreground">
              Statut des services backend AGI
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Rafraîchir
          </Button>
        </div>

        <Card className="border-border bg-card">
          <CardContent className="p-6 text-center space-y-4">
            <div className="flex justify-center">
              <ShieldAlert className="h-12 w-12 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-foreground font-medium">
                Backend déconnecté
              </h3>
              <p className="text-muted-foreground text-sm">
                Impossible de contacter le serveur GraphQL. L'interface
                fonctionne en mode démo.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
              className="text-foreground"
            >
              Réessayer
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>Health</h2>
          <p className="text-muted-foreground">
            Statut temps réel des services backend AGI
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={loading}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Rafraîchir
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Services surveillés</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <>
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </>
          ) : statuses.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              Aucune donnée disponible
            </p>
          ) : (
            statuses.map((status) => (
              <div
                key={status.service}
                className="flex items-center justify-between rounded border border-border bg-card py-3 px-4 hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Activity className="h-4 w-4 text-foreground" />
                  <div>
                    <p className="text-foreground">{status.service}</p>
                    {status.message && (
                      <p className="text-muted-foreground text-sm">
                        {status.message}
                      </p>
                    )}
                  </div>
                </div>
                <Badge variant={status.status ? 'outline' : 'destructive'}>
                  {status.status ? 'OK' : 'OFF'}
                </Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Alertes</CardTitle>
          <Badge variant={critical.length > 0 ? 'destructive' : 'outline'}>
            {critical.length > 0
              ? `${critical.length} service(s) à corriger`
              : 'Aucune alerte'}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-2">
          {critical.length === 0 ? (
            <p className="text-muted-foreground">Infrastructure stable.</p>
          ) : (
            critical.map((item) => (
              <div
                key={item.service}
                className="flex items-center gap-2 rounded border border-border bg-accent px-3 py-2"
              >
                <ShieldAlert className="h-4 w-4 text-foreground" />
                <span className="text-foreground text-sm">
                  {item.service} : {item.message ?? 'Erreur détectée'}
                </span>
              </div>
            ))
          )}
          {error && statuses.length === 0 && (
            <div className="mt-4 p-3 rounded border border-border bg-muted">
              <p className="text-muted-foreground text-sm">
                Mode démo: Backend inaccessible
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
