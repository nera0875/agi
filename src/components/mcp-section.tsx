import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Switch } from "./ui/switch";
import { Badge } from "./ui/badge";
import { RefreshCw, Heart, Trash2 } from "lucide-react";
import { useState } from "react";

interface MCPServer {
  id: string;
  name: string;
  package: string;
  version: string;
  status: 'configured' | 'running';
  chatEnabled: boolean;
}

const mockServers: MCPServer[] = [
  {
    id: '1',
    name: 'notion',
    package: 'npx',
    version: 'notion npx',
    status: 'configured',
    chatEnabled: true
  },
  {
    id: '2',
    name: 'browserbase',
    package: 'npx',
    version: 'b55bc npx',
    status: 'configured',
    chatEnabled: true
  },
  {
    id: '3',
    name: 'sentry',
    package: 'npx',
    version: 'sl8bc npx',
    status: 'configured',
    chatEnabled: true
  },
  {
    id: '4',
    name: 'memory',
    package: 'python3',
    version: 'sl8bc python3',
    status: 'configured',
    chatEnabled: true
  }
];

export function MCPSection() {
  const [servers, setServers] = useState<MCPServer[]>(mockServers);
  const [packageUrl, setPackageUrl] = useState('');

  const handleToggleChat = (serverId: string) => {
    setServers(servers.map(s => 
      s.id === serverId ? { ...s, chatEnabled: !s.chatEnabled } : s
    ));
  };

  const handleDeleteServer = (serverId: string) => {
    setServers(servers.filter(s => s.id !== serverId));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>MCP Servers</h2>
          <p className="text-muted-foreground">
            Manage Model Context Protocol servers on this VPS
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" size="sm">
            <Heart className="h-4 w-4 mr-2" />
            Check Health
          </Button>
          <Button variant="secondary" size="sm">
            Export
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Install New MCP Server</CardTitle>
          <CardDescription>
            Enter npm package name or HTTP/HTTPS URL. Rollback Claude Code after installation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input 
              placeholder="Package name or HTTP/HTTPS URL"
              value={packageUrl}
              onChange={(e) => setPackageUrl(e.target.value)}
              className="flex-1"
            />
            <Button>Next</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Installed Servers ({servers.length})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {servers.map((server) => (
            <div 
              key={server.id}
              className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                  <Settings className="h-5 w-5 text-muted-foreground" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4>{server.name}</h4>
                    <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
                      {server.status}
                    </Badge>
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/20">
                      Chat: {server.chatEnabled ? 'ON' : 'OFF'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {server.package}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {server.version}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Switch 
                  checked={server.chatEnabled}
                  onCheckedChange={() => handleToggleChat(server.id)}
                />
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => handleDeleteServer(server.id)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
