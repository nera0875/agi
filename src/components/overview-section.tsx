import { useEffect, useMemo, useState } from 'react';
import { Activity, Brain, Database, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Skeleton } from './ui/skeleton';
import { DatabaseViewer } from './database-viewer';
import { toast } from 'sonner';
import {
  HealthStatus,
  SearchResult,
  useHealthStatuses,
  useLazySearchMemories,
} from '../lib/graphql-hooks';

type ServiceCard = {
  id: string;
  title: string;
  icon: typeof Database;
  status?: HealthStatus;
};

interface OverviewSectionProps {
  onNavigate?: (section: string) => void;
}

const SERVICE_LABELS: ServiceCard[] = [
  { id: 'database', title: 'PostgreSQL', icon: Database },
  { id: 'redis', title: 'Redis', icon: Zap },
  { id: 'memory_embeddings', title: 'Embeddings', icon: Brain },
  { id: 'memory_rag', title: 'RAG Pipeline', icon: Activity },
];

export function OverviewSection({ onNavigate }: OverviewSectionProps) {
  const [searchQuery, setSearchQuery] = useState('architecture AGI');
  const [latestResults, setLatestResults] = useState<SearchResult[]>([]);
  const {
    data: healthStatuses,
    loading: healthLoading,
    error: healthError,
  } = useHealthStatuses();
  const [runSearch, { loading: searchLoading, error: searchError }] =
    useLazySearchMemories();

  useEffect(() => {
    const runInitialSearch = async () => {
      try {
        const results = await runSearch({
          query: searchQuery,
          topK: 3,
        });
        setLatestResults(results);
      } catch (err) {
        // Backend offline - no results
        setLatestResults([]);
      }
    };
    runInitialSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cards = useMemo(() => {
    return SERVICE_LABELS.map((service) => ({
      ...service,
      status: healthStatuses.find((item) =>
        item.service.includes(service.id)
      ),
    }));
  }, [healthStatuses]);

  const overallHealthy = useMemo(() => {
    if (!healthStatuses.length) {
      return undefined;
    }
    return healthStatuses.every((status) => status.status);
  }, [healthStatuses]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      return;
    }
    try {
      const results = await runSearch({
        query: searchQuery,
        topK: 5,
      });
      setLatestResults(results);
      if (results.length === 0 && searchError) {
        toast.info('Aucune mémoire trouvée - Backend déconnecté', {
          duration: 2000,
        });
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Erreur inconnue';
      console.warn('Search error:', errorMsg);
      toast.info('Recherche indisponible - Backend déconnecté', {
        description: 'Mode démo activé',
      });
      setLatestResults([]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>Vue d&apos;ensemble</h2>
          <p className="text-muted-foreground">
            Statut du backend AGI et recherche mémoire rapide
          </p>
        </div>
        <Badge
          variant={overallHealthy ? "outline" : "destructive"}
          className={overallHealthy ? "" : "border-destructive/40"}
        >
          {overallHealthy === undefined
            ? "Vérification…"
            : overallHealthy
            ? "Opérationnel"
            : "Dégradé"}
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ id, title, icon: Icon, status }) => (
          <Card key={id} className="border-muted/60">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-muted-foreground flex items-center gap-2">
                <Icon className="h-4 w-4 text-primary" />
                {title}
              </CardTitle>
              <Badge
                variant={status?.status ? "outline" : "destructive"}
                className="text-xs"
              >
                {status?.status ? "OK" : "OFF"}
              </Badge>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {healthLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : status ? (
                <span>{status.message ?? "En ligne"}</span>
              ) : (
                <span>En attente d&apos;implémentation</span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recherche rapide</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Rechercher dans les mémoires (ex: architecture, embeddings...)"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
            />
            <Button onClick={handleSearch} disabled={searchLoading}>
              Rechercher
            </Button>
          </div>
          {searchError && (
            <p className="text-sm text-destructive">
              Erreur lors de la recherche : {searchError.message}
            </p>
          )}
          <div className="space-y-3">
            {searchLoading && (
              <div className="space-y-2">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            )}
            {!searchLoading && latestResults.length === 0 && (
              <p className="text-sm text-muted-foreground">
                Aucune mémoire disponible pour le moment.
              </p>
            )}
            {latestResults.map((result) => (
              <Card key={result.memory.id} className="border-muted/60">
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <h4 className="text-foreground">
                        {result.memory.metadata?.title ??
                          result.memory.content.slice(0, 96)}
                      </h4>
                      <p className="text-muted-foreground">
                        {result.memory.content}
                      </p>
                    </div>
                    {result.memory.similarityScore !== undefined && (
                      <Badge variant="outline">
                        {(result.memory.similarityScore ?? 0).toFixed(2)}
                      </Badge>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(() => {
                      const metadata =
                        (result.memory.metadata ?? {}) as Record<
                          string,
                          unknown
                        >;
                      const tagsRaw = metadata["tags"];
                      if (Array.isArray(tagsRaw) && tagsRaw.length > 0) {
                        return (tagsRaw as string[]).slice(0, 4).map((tag) => (
                          <Badge key={tag} variant="secondary">
                            {tag}
                          </Badge>
                        ));
                      }
                      return (
                        <Badge variant="secondary">
                          source: {result.memory.sourceType}
                        </Badge>
                      );
                    })()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {healthError && healthStatuses.length === 0 && (
        <Card className="border-border bg-muted">
          <CardContent className="p-4">
            <p className="text-muted-foreground text-sm">
              Mode démo: Backend déconnecté. Certaines données ne sont pas disponibles.
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Bases de données AGI</CardTitle>
        </CardHeader>
        <CardContent>
          <DatabaseViewer />
        </CardContent>
      </Card>
    </div>
  );
}
