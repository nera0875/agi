import { useState } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "./components/ui/sidebar";
import {
  LayoutDashboard,
  Settings,
  Calendar,
  Clock,
  MessageSquare,
  CheckSquare,
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Toaster } from "./components/ui/sonner";
import { AGIChatContainer } from "./components/AGIChatContainer";
import { TasksPage } from "./pages/TasksPage";

type Section = "tasks" | "calendar" | "timeblocks" | "chat" | "settings";

const navigationItems = [
  {
    id: "tasks" as Section,
    title: "Task Manager",
    icon: CheckSquare,
  },
  {
    id: "calendar" as Section,
    title: "Calendrier",
    icon: Calendar,
  },
  {
    id: "timeblocks" as Section,
    title: "Blocs de temps",
    icon: Clock,
  },
  {
    id: "chat" as Section,
    title: "Chat AGI",
    icon: MessageSquare,
  },
  {
    id: "settings" as Section,
    title: "Paramètres",
    icon: Settings,
  },
];

function App() {
  const [activeSection, setActiveSection] = useState<Section>("tasks");

  const renderContent = () => {
    switch (activeSection) {
      case "tasks":
        return <TasksPage />;
      case "calendar":
        return (
          <Card>
            <CardHeader>
              <CardTitle>Calendrier</CardTitle>
              <CardDescription>
                Visualisez et gérez vos blocs de temps dans une vue calendrier
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Interface calendrier à implémenter selon les maquettes Figma
              </p>
            </CardContent>
          </Card>
        );
      case "timeblocks":
        return (
          <Card>
            <CardHeader>
              <CardTitle>Blocs de temps</CardTitle>
              <CardDescription>
                Créez et organisez vos blocs de temps avec l'IA
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Interface de gestion des blocs de temps à implémenter
              </p>
            </CardContent>
          </Card>
        );
      case "chat":
        return (
          <div className="h-full">
            <AGIChatContainer
              userId="demo-user"
              showMemoryStats={true}
              showControls={true}
              apiEndpoint="/api/chat"
              className="h-full border rounded-lg"
            />
          </div>
        );
      case "settings":
        return (
          <Card>
            <CardHeader>
              <CardTitle>Paramètres</CardTitle>
              <CardDescription>
                Configurez votre application et vos préférences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Interface de paramètres à implémenter
              </p>
            </CardContent>
          </Card>
        );
      default:
        return null;
    }
  };

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full">
        <Sidebar>
          <SidebarHeader>
            <div className="flex items-center gap-2 px-4 py-2">
              <LayoutDashboard className="h-6 w-6" />
              <span className="font-semibold">AGI Time Blocking</span>
            </div>
          </SidebarHeader>
          
          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Navigation</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navigationItems.map((item) => (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton
                        onClick={() => setActiveSection(item.id)}
                        isActive={activeSection === item.id}
                      >
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
          
          <SidebarFooter>
            <div className="p-4">
              <p className="text-xs text-muted-foreground">
                Version 1.0.0 - Clean Architecture
              </p>
            </div>
          </SidebarFooter>
        </Sidebar>

        <div className="flex-1 flex flex-col">
          <header className="border-b border-border bg-card">
            <div className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-4">
                <SidebarTrigger />
                <h1 className="text-xl font-semibold">
                  {navigationItems.find(item => item.id === activeSection)?.title}
                </h1>
              </div>
              
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  Synchroniser
                </Button>
                <Button size="sm">
                  Nouveau
                </Button>
              </div>
            </div>
          </header>

          <main className={`flex-1 overflow-auto ${activeSection === 'chat' || activeSection === 'tasks' ? 'p-0' : 'p-6'}`}>
            {renderContent()}
          </main>
        </div>
      </div>
      
      <Toaster />
    </SidebarProvider>
  );
}

export default App;
