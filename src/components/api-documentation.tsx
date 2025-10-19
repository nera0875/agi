import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Code, Database, Link as LinkIcon, Trash2, Edit, Plus } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import { graphqlEndpoint } from '../config/api';

const queries = [
  {
    name: "databaseSchema",
    type: "Query",
    description: "Récupère le schéma complet de la base Neo4j (labels et types de relations)",
    example: `query {
  databaseSchema {
    success
    labels {
      name
      count
    }
    relationshipTypes {
      name
    }
  }
}`,
  },
  {
    name: "databaseNodes",
    type: "Query",
    description: "Récupère les nœuds d'un label spécifique (retourne des JSON strings à parser)",
    example: `query {
  databaseNodes(label: "Memory", limit: 50, offset: 0) {
    properties
  }
}`,
  },
  {
    name: "databaseQuery",
    type: "Query",
    description: "Exécute une requête Cypher personnalisée",
    example: `query {
  databaseQuery(
    cypher: "MATCH (n:Memory) WHERE n.type = $type RETURN n LIMIT 10",
    parameters: "{\\"type\\": \\"context\\"}"
  ) {
    success
    data
    count
    message
  }
}`,
  },
];

const mutations = [
  {
    name: "createNode",
    type: "Mutation",
    description: "Crée un nouveau nœud Neo4j",
    example: `mutation {
  createNode(input: {
    label: "Memory",
    properties: "{\\"content\\":\\"Test\\",\\"type\\":\\"context\\",\\"created_at\\":\\"2025-10-15\\"}"
  }) {
    success
    nodeId
    message
  }
}`,
  },
  {
    name: "updateNode",
    type: "Mutation",
    description: "Met à jour un nœud existant",
    example: `mutation {
  updateNode(
    nodeId: "4:abc123",
    properties: "{\\"content\\":\\"Updated\\",\\"updated_at\\":\\"2025-10-15\\"}"
  ) {
    success
    data
    message
  }
}`,
  },
  {
    name: "deleteNode",
    type: "Mutation",
    description: "Supprime un nœud",
    example: `mutation {
  deleteNode(nodeId: "4:abc123") {
    success
    count
    message
  }
}`,
  },
  {
    name: "createRelationship",
    type: "Mutation",
    description: "Crée une relation entre deux nœuds",
    example: `mutation {
  createRelationship(input: {
    sourceId: "4:node1",
    targetId: "4:node2",
    relationshipType: "RELATES_TO",
    properties: "{\\"strength\\": 0.9}"
  }) {
    success
    relationshipId
    message
  }
}`,
  },
];

const tips = [
  {
    title: "Parser les properties",
    description: "Tous les 'properties' sont des JSON strings",
    code: `const node = JSON.parse(properties);
console.log(node.content);`,
  },
  {
    title: "Format Node ID",
    description: "Les IDs Neo4j utilisent le format : '4:abc123def'",
    code: `nodeId: "4:abc123def"`,
  },
  {
    title: "Gestion des erreurs",
    description: "Le système bascule automatiquement en mock si l'API est offline",
    code: `// Pas besoin de try/catch
// Le fallback est automatique`,
  },
];

export function APIDocumentation() {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copié dans le presse-papier");
  };

  return (
    <div className="space-y-6">
      <div>
        <h2>Documentation API</h2>
        <p className="text-muted-foreground">
          Guide complet des requêtes GraphQL disponibles
        </p>
      </div>

      <Card className="bg-chart-1/5 border-chart-1/20">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Database className="h-4 w-4" />
            Endpoint GraphQL
          </CardTitle>
        </CardHeader>
        <CardContent>
          <code className="text-sm bg-muted px-3 py-2 rounded block">
            {graphqlEndpoint}
          </code>
        </CardContent>
      </Card>

      <Tabs defaultValue="queries" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="queries">
            <Database className="h-4 w-4 mr-2" />
            Queries
          </TabsTrigger>
          <TabsTrigger value="mutations">
            <Edit className="h-4 w-4 mr-2" />
            Mutations
          </TabsTrigger>
          <TabsTrigger value="tips">
            <Code className="h-4 w-4 mr-2" />
            Tips
          </TabsTrigger>
        </TabsList>

        <TabsContent value="queries" className="space-y-4">
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {queries.map((query) => (
                <Card key={query.name}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">{query.name}</CardTitle>
                        <CardDescription className="mt-1">
                          {query.description}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="bg-chart-2/10 text-chart-2 border-chart-2/20">
                        {query.type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="relative">
                      <pre className="bg-muted p-4 rounded-lg text-xs overflow-x-auto">
                        <code>{query.example}</code>
                      </pre>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-2 right-2"
                        onClick={() => copyToClipboard(query.example)}
                      >
                        Copier
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="mutations" className="space-y-4">
          <ScrollArea className="h-[600px] pr-4">
            <div className="space-y-4">
              {mutations.map((mutation) => (
                <Card key={mutation.name}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base flex items-center gap-2">
                          {mutation.name === 'createNode' && <Plus className="h-4 w-4" />}
                          {mutation.name === 'updateNode' && <Edit className="h-4 w-4" />}
                          {mutation.name === 'deleteNode' && <Trash2 className="h-4 w-4" />}
                          {mutation.name === 'createRelationship' && <LinkIcon className="h-4 w-4" />}
                          {mutation.name}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {mutation.description}
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="bg-chart-4/10 text-chart-4 border-chart-4/20">
                        {mutation.type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="relative">
                      <pre className="bg-muted p-4 rounded-lg text-xs overflow-x-auto">
                        <code>{mutation.example}</code>
                      </pre>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="absolute top-2 right-2"
                        onClick={() => copyToClipboard(mutation.example)}
                      >
                        Copier
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="tips" className="space-y-4">
          <div className="space-y-4">
            {tips.map((tip, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-base">{tip.title}</CardTitle>
                  <CardDescription>{tip.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded-lg text-xs overflow-x-auto">
                    <code>{tip.code}</code>
                  </pre>
                </CardContent>
              </Card>
            ))}

            <Card className="bg-chart-4/5 border-chart-4/20">
              <CardHeader>
                <CardTitle className="text-base">⚠️ Important</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Toutes les properties sont en JSON string → Parser avec JSON.parse()</p>
                <p>• Node IDs au format Neo4j : "4:abc123def"</p>
                <p>• Cypher queries via databaseQuery() pour requêtes custom</p>
                <p>• CORS ouvert en DEV → Tous domaines acceptés</p>
                <p>• Fallback automatique en mock si API offline</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
