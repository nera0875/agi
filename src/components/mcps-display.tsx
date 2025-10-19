import { useAllMCPs } from "@/lib/graphql-hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";

export function MCPsDisplay() {
  const { data: mcps, loading, error } = useAllMCPs();

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
          Erreur lors du chargement des MCPs: {error.message}
        </AlertDescription>
      </Alert>
    );
  }

  if (!mcps || mcps.length === 0) {
    return (
      <Alert>
        <AlertDescription>Aucun MCP connu trouvé</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {mcps.map((mcp) => (
        <div
          key={mcp.id}
          className="rounded-lg border bg-white p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-semibold text-sm text-gray-900">
                {mcp.display_name}
              </h3>
              <p className="text-xs text-gray-500 mt-1">
                ID: {mcp.mcp_id} • Utilisé: {mcp.usage_count} fois
              </p>
            </div>
          </div>

          {mcp.description && (
            <p className="text-sm text-gray-700 mb-3">{mcp.description}</p>
          )}

          {mcp.capabilities.length > 0 && (
            <div className="mb-3">
              <p className="text-xs font-medium text-gray-600 mb-2">
                Capacités:
              </p>
              <div className="flex flex-wrap gap-2">
                {mcp.capabilities.map((capability) => (
                  <Badge key={capability} variant="outline" className="text-xs">
                    {capability}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {mcp.last_used_at && (
            <div className="text-xs text-gray-500">
              Dernière utilisation:{" "}
              {format(new Date(mcp.last_used_at), "dd/MM/yyyy HH:mm")}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
