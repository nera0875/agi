import { useState, useCallback, useRef, useEffect } from "react";
import { KnowledgeGraph } from "./knowledge-graph";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Search, RefreshCw, Download, Maximize2, ZoomIn, ZoomOut, Filter } from "lucide-react";
import { Skeleton } from "./ui/skeleton";
import { useGraphData, type GraphNode, type GraphRelation } from "../lib/graphql-hooks";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Checkbox } from "./ui/checkbox";
import { Label } from "./ui/label";

export function Neo4jSection() {
  const [nodeTypes, setNodeTypes] = useState<string[]>(["Memory", "Knowledge", "Task"]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<any>(null);

  // Fetch graph data
  const { data: graphData, loading, error, refetch } = useGraphData({
    nodeTypes: nodeTypes.length > 0 ? nodeTypes : undefined,
    limit: 100,
  });

  // Update graph dimensions based on container size
  useEffect(() => {
    if (containerRef.current) {
      const updateDimensions = () => {
        if (containerRef.current) {
          setGraphDimensions({
            width: containerRef.current.offsetWidth,
            height: Math.max(600, window.innerHeight - 400),
          });
        }
      };

      updateDimensions();
      window.addEventListener("resize", updateDimensions);
      return () => window.removeEventListener("resize", updateDimensions);
    }
  }, []);

  // Transform data for force-graph
  const transformedData = {
    nodes: graphData?.nodes.map((node) => ({
      id: node.id,
      name: node.label,
      type: node.type,
      properties: node.properties,
      val: 5, // Node size
    })) || [],
    links: graphData?.relations.map((rel) => ({
      source: rel.source,
      target: rel.target,
      label: rel.type,
      weight: rel.weight,
    })) || [],
  };

  // Node color based on type
  const getNodeColor = (node: any) => {
    switch (node.type) {
      case "Memory":
        return "#3b82f6"; // blue
      case "Knowledge":
        return "#10b981"; // green
      case "Task":
        return "#f59e0b"; // amber
      default:
        return "#6b7280"; // gray
    }
  };

  // Handle node click
  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    // Center camera on node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  }, []);

  // Toggle node type filter
  const toggleNodeType = (type: string) => {
    setNodeTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    );
  };

  // Export graph as JSON
  const exportGraph = () => {
    const dataStr = JSON.stringify(graphData, null, 2);
    const dataUri = "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `graph-data-${new Date().toISOString()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  // Zoom controls
  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() * 1.5, 300);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(graphRef.current.zoom() / 1.5, 300);
    }
  };

  const handleZoomFit = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2>Knowledge Graph</h2>
        <p className="text-muted-foreground">
          Visualisation interactive du graphe de connaissances (Memory + Knowledge + Tasks)
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Nodes</CardDescription>
            <CardTitle className="text-2xl">
              {graphData?.nodes.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Relations</CardDescription>
            <CardTitle className="text-2xl">
              {graphData?.relations.length || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Graph Density</CardDescription>
            <CardTitle className="text-2xl">
              {graphData?.nodes.length && graphData?.relations.length
                ? (
                    (graphData.relations.length / (graphData.nodes.length * (graphData.nodes.length - 1))) * 100
                  ).toFixed(1)
                : "0.0"}%
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Tabs defaultValue="graph" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="graph">Graph Visualization</TabsTrigger>
          <TabsTrigger value="data">Raw Data</TabsTrigger>
        </TabsList>

        {/* Graph Tab */}
        <TabsContent value="graph" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Interactive Graph</CardTitle>
                  <CardDescription>
                    Cliquez sur un nœud pour voir ses détails • Glissez pour déplacer
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="icon" onClick={handleZoomIn} title="Zoom In">
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" onClick={handleZoomOut} title="Zoom Out">
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" onClick={handleZoomFit} title="Fit to Screen">
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" onClick={() => refetch()} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  </Button>
                  <Button variant="outline" size="icon" onClick={exportGraph} disabled={!graphData}>
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Filters */}
              <div className="flex items-center gap-4 border rounded-lg p-4 bg-muted/30">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <div className="flex items-center gap-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="filter-memory"
                      checked={nodeTypes.includes("Memory")}
                      onCheckedChange={() => toggleNodeType("Memory")}
                    />
                    <Label htmlFor="filter-memory" className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-blue-500" />
                      Memory
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="filter-knowledge"
                      checked={nodeTypes.includes("Knowledge")}
                      onCheckedChange={() => toggleNodeType("Knowledge")}
                    />
                    <Label htmlFor="filter-knowledge" className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-green-500" />
                      Knowledge
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="filter-task"
                      checked={nodeTypes.includes("Task")}
                      onCheckedChange={() => toggleNodeType("Task")}
                    />
                    <Label htmlFor="filter-task" className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-amber-500" />
                      Task
                    </Label>
                  </div>
                </div>
              </div>

              {/* Graph Visualization */}
              {loading ? (
                <div className="space-y-2">
                  <Skeleton className="h-[600px] w-full" />
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-[600px] border rounded-lg">
                  <div className="text-center">
                    <p className="text-sm text-destructive">Erreur de chargement du graphe</p>
                    <p className="text-xs text-muted-foreground mt-1">{error.message}</p>
                  </div>
                </div>
              ) : transformedData.nodes.length === 0 ? (
                <div className="flex items-center justify-center h-[600px] border rounded-lg">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">Aucun nœud trouvé</p>
                    <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Recharger
                    </Button>
                  </div>
                </div>
              ) : (
                <KnowledgeGraph
                  nodes={graphData?.nodes || []}
                  relations={graphData?.relations || []}
                />
              )}

              {/* Selected Node Details */}
              {selectedNode && (
                <Card className="border-primary">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: getNodeColor(selectedNode) }}
                          />
                          {selectedNode.name}
                        </CardTitle>
                        <CardDescription>
                          <Badge variant="outline">{selectedNode.type}</Badge>
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedNode(null)}
                      >
                        ×
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="text-sm">
                      <p className="font-medium">Properties:</p>
                      <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-40">
                        {JSON.stringify(selectedNode.properties, null, 2)}
                      </pre>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Data Tab */}
        <TabsContent value="data" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Raw Graph Data</CardTitle>
              <CardDescription>Nodes et relations en format JSON</CardDescription>
            </CardHeader>
            <CardContent>
              <pre className="p-4 bg-muted rounded text-xs overflow-auto max-h-[600px]">
                {JSON.stringify(graphData, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
