import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Button } from "./ui/button";
import { RefreshCw, Download } from "lucide-react";
import { graphqlFetch } from "../lib/graphql-client";
import { Skeleton } from "./ui/skeleton";

interface Session {
  id: string;
  timestamp: string;
  duration: number;
  status: string;
}

export function BCIDataSection() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSessions = async () => {
    try {
      setRefreshing(true);
      // Exemple de requête - adapter selon votre schema GraphQL
      const data = await graphqlFetch<{ sessions: Session[] }>(
        `query {
          sessions(limit: 10) {
            id
            timestamp
            duration
            status
          }
        }`
      );
      setSessions(data.sessions);
    } catch (err) {
      // Données mockées pour la démo
      setSessions([
        {
          id: "1",
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          duration: 1200,
          status: "completed",
        },
        {
          id: "2",
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          duration: 1800,
          status: "completed",
        },
        {
          id: "3",
          timestamp: new Date(Date.now() - 10800000).toISOString(),
          duration: 900,
          status: "failed",
        },
        {
          id: "4",
          timestamp: new Date(Date.now() - 14400000).toISOString(),
          duration: 1500,
          status: "completed",
        },
        {
          id: "5",
          timestamp: new Date(Date.now() - 18000000).toISOString(),
          duration: 2100,
          status: "in_progress",
        },
      ]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="default" className="bg-chart-2">Terminé</Badge>;
      case "in_progress":
        return <Badge variant="default" className="bg-chart-4">En cours</Badge>;
      case "failed":
        return <Badge variant="destructive">Échoué</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const formatTimestamp = (iso: string) => {
    const date = new Date(iso);
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>Données BCI</h2>
          <p className="text-muted-foreground">
            Sessions et signaux enregistrés
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchSessions}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Exporter
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sessions récentes</CardTitle>
          <CardDescription>
            Liste des dernières sessions d'enregistrement BCI
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID Session</TableHead>
                  <TableHead>Date/Heure</TableHead>
                  <TableHead>Durée</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((session) => (
                  <TableRow key={session.id}>
                    <TableCell className="font-mono">{session.id}</TableCell>
                    <TableCell>{formatTimestamp(session.timestamp)}</TableCell>
                    <TableCell>{formatDuration(session.duration)}</TableCell>
                    <TableCell>{getStatusBadge(session.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        Voir détails
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
