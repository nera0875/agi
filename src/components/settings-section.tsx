import { useState } from "react";
import { Server, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { toast } from "sonner";
import { graphqlEndpoint } from "../config/api";

export function SettingsSection() {
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState<"idle" | "ok" | "error">("idle");

  const handleTestConnection = async () => {
    setTesting(true);
    setStatus("idle");
    try {
      const response = await fetch(graphqlEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "{ healthCheck { service } }" }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json();
      if (payload.errors) {
        throw new Error(payload.errors[0]?.message ?? "Erreur GraphQL");
      }

      setStatus("ok");
      toast.success("Connexion réussie");
    } catch (error) {
      setStatus("error");
      toast.error("Connexion échouée", {
        description:
          error instanceof Error ? error.message : "Erreur inconnue",
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2>Paramètres</h2>
        <p className="text-muted-foreground">
          Configuration minimale en attendant les services avancés.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-4 w-4" />
            Endpoint GraphQL
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input value={graphqlEndpoint} readOnly />
          <div className="flex items-center gap-3">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(graphqlEndpoint);
                toast.success("Endpoint copié");
              }}
            >
              Copier
            </Button>
            <Button
              size="sm"
              onClick={handleTestConnection}
              disabled={testing}
            >
              Tester
            </Button>
            {status === "ok" && (
              <Badge variant="default">
                Connecté
              </Badge>
            )}
            {status === "error" && (
              <Badge variant="destructive">Erreur</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="border border-dashed border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Fonctionnalités à venir
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-muted-foreground">
          <p>• Gestion des secrets (API keys, configuration agents)</p>
          <p>• Paramétrage des workflows LangGraph</p>
          <p>• Intégration monitoring (Sentry, LangSmith)</p>
        </CardContent>
      </Card>
    </div>
  );
}
