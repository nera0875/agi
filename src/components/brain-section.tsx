import { useMemo, useState } from "react";
import {
  Database,
  Link,
  Plus,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import {
  useCreateMemory,
  useSearchMemories,
  SearchResult,
} from "../lib/graphql-hooks";
import { Neo4jSection } from "./neo4j-section";
import { toast } from "sonner";

export function BrainSection() {
  // Load active tab from localStorage
  const [activeTab, setActiveTab] = useState(() => {
    const stored = localStorage.getItem('brain-active-tab');
    return stored || "memory";
  });

  const [searchQuery, setSearchQuery] = useState("architecture");
  const [newMemory, setNewMemory] = useState("");
  const [newTags, setNewTags] = useState("");

  // Save active tab to localStorage
  const handleTabChange = (value: string) => {
    setActiveTab(value);
    localStorage.setItem('brain-active-tab', value);
  };

  const {
    data: searchResults,
    loading: searchLoading,
    error: searchError,
    refetch,
  } = useSearchMemories(
    { query: searchQuery, topK: 8 },
    { skip: !searchQuery.trim() }
  );

  // Handle offline search gracefully
  if (searchError) {
    toast.info("Mode démo: Recherche hors ligne", { duration: 2000 });
  }

  const [createMemory, { loading: createLoading }] = useCreateMemory({
    onCompleted: () => {
      toast.success("Mémoire enregistrée");
      setNewMemory("");
      setNewTags("");
      refetch();
    },
    onError: (error) => {
      toast.error("Création échouée", {
        description: error.message,
      });
    },
  });

  const tagsList = useMemo(() => {
    return newTags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);
  }, [newTags]);

  const handleCreate = async () => {
    if (!newMemory.trim()) {
      toast.error("Le contenu est requis");
      return;
    }

    await createMemory({
      content: newMemory,
      metadata: {
        tags: tagsList,
        createdAt: new Date().toISOString(),
      },
    });
  };

  const renderResults = (results: SearchResult[]) => {
    if (searchLoading) {
      return (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-20 w-full" />
          ))}
        </div>
      );
    }

    if (results.length === 0) {
      return (
        <p className="text-muted-foreground">
          Aucune mémoire trouvée pour &laquo;{searchQuery}&raquo;.
        </p>
      );
    }

    return (
      <div className="space-y-3">
        {results.map((result) => {
          const metadata = (result.memory.metadata ?? {}) as Record<
            string,
            unknown
          >;
          const tags = Array.isArray(metadata["tags"])
            ? (metadata["tags"] as string[])
            : [];

          return (
            <Card key={result.memory.id} className="border-muted/60">
              <CardContent className="space-y-2 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1">
                    <p className="text-foreground">
                      {result.memory.content}
                    </p>
                    <div className="flex flex-wrap gap-2 text-muted-foreground">
                      <span>ID: {result.memory.id}</span>
                      <span>•</span>
                      <span>Source: {result.memory.sourceType}</span>
                    </div>
                  </div>
                  {result.memory.similarityScore !== undefined && (
                    <Badge variant="outline">
                      {(result.memory.similarityScore ?? 0).toFixed(2)}
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {tags.length > 0 ? (
                    tags.slice(0, 5).map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))
                  ) : (
                    <Badge variant="secondary">Sans tag</Badge>
                  )}
                </div>
                {result.highlights.length > 0 && (
                  <p className="text-muted-foreground">
                    Highlight : {result.highlights[0]}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2>Brain</h2>
        <p className="text-muted-foreground">
          Mémoire vectorielle et futures intégrations graph.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="memory">
            <Database className="h-4 w-4 mr-2" />
            Memory
          </TabsTrigger>
          <TabsTrigger value="graph">
            <Link className="h-4 w-4 mr-2" />
            Graph
          </TabsTrigger>
        </TabsList>

        <TabsContent value="memory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recherche</CardTitle>
              <CardDescription>
                Basée sur la requête GraphQL `searchMemories`
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Rechercher une mémoire..."
                    className="pl-9"
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        refetch();
                      }
                    }}
                  />
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => refetch()}
                  disabled={searchLoading}
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              {renderResults(searchResults)}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Ajouter une mémoire</CardTitle>
              <CardDescription>
                Utilise la mutation GraphQL `createMemory`
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={newMemory}
                onChange={(event) => setNewMemory(event.target.value)}
                placeholder="Décrivez le contexte à mémoriser..."
                rows={5}
              />
              <Input
                value={newTags}
                onChange={(event) => setNewTags(event.target.value)}
                placeholder="Tags (séparés par une virgule)"
              />
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2 text-muted-foreground">
                  {tagsList.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                  {tagsList.length === 0 && (
                    <span className="text-muted-foreground/80">
                      Aucun tag pour le moment
                    </span>
                  )}
                </div>
                <Button onClick={handleCreate} disabled={createLoading}>
                  <Plus className="h-4 w-4 mr-2" />
                  Enregistrer
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="graph">
          <Neo4jSection />
        </TabsContent>
      </Tabs>
    </div>
  );
}
