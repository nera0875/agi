import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { KnowledgeDisplay } from "./knowledge-display";
import { RoadmapDisplay } from "./roadmap-display";
import { TasksDisplay } from "./tasks-display";
import { MCPsDisplay } from "./mcps-display";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function DatabaseViewer() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Système AGI</h2>
          <p className="text-sm text-gray-500 mt-1">
            Visualisez les données de votre base de données
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Actualiser
        </Button>
      </div>

      <Tabs defaultValue="knowledge" className="w-full flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-4 mb-6">
          <TabsTrigger value="knowledge">Connaissances</TabsTrigger>
          <TabsTrigger value="roadmap">Feuille de route</TabsTrigger>
          <TabsTrigger value="tasks">Tâches</TabsTrigger>
          <TabsTrigger value="mcps">MCPs</TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-auto">
          <TabsContent value="knowledge" className="mt-0 space-y-4">
            <KnowledgeDisplay key={`knowledge-${refreshKey}`} />
          </TabsContent>

          <TabsContent value="roadmap" className="mt-0 space-y-4">
            <RoadmapDisplay key={`roadmap-${refreshKey}`} />
          </TabsContent>

          <TabsContent value="tasks" className="mt-0 space-y-4">
            <TasksDisplay key={`tasks-${refreshKey}`} />
          </TabsContent>

          <TabsContent value="mcps" className="mt-0 space-y-4">
            <MCPsDisplay key={`mcps-${refreshKey}`} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
