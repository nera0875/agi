import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion";
import { ScrollArea } from "./ui/scroll-area";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Skeleton } from "./ui/skeleton";
import { 
  FolderOpen,
  Terminal as TerminalIcon,
  Shield,
  Code2,
  Key,
  ScrollText,
  Plus,
  Search,
  RefreshCw,
  Download,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Heart,
  AlertCircle,
  Info,
  CheckCircle,
  XCircle,
  File,
  Folder,
  Home,
  BookOpen,
  Save,
  Settings,
  Activity,
} from "lucide-react";
import { useState } from "react";

// ============= MOCK DATA =============

const mockFiles = [
  { name: '.claude', type: 'folder', path: '/home/zt1nkz/projects/BCI/.claude' },
  { name: '.git', type: 'folder', path: '/home/zt1nkz/projects/BCI/.git' },
  { name: 'backend', type: 'folder', path: '/home/zt1nkz/projects/BCI/backend' },
  { name: 'docs', type: 'folder', path: '/home/zt1nkz/projects/BCI/docs' },
  { name: 'mcp-servers', type: 'folder', path: '/home/zt1nkz/projects/BCI/mcp-servers' },
  { name: 'brain.py', type: 'file', path: '/home/zt1nkz/projects/BCI/backend/brain.py' },
  { name: 'requirements.txt', type: 'file', path: '/home/zt1nkz/projects/BCI/requirements.txt' },
  { name: 'README.md', type: 'file', path: '/home/zt1nkz/projects/BCI/README.md' }
];

const mockFileContent = `# Password root : Valtorin789

# Réponds direct. Décide seul, avance vite. Chaque token coûte de l'argent.

## 💡 MCP Tools

**Mémoire utilisée** :
- DDG2 : MCP Management API
- DDG3 : MCP Server API  
- DDG1 : Chat websocket
- 6331 : Qdrant Vector DB
- 7687 : Neo4j graph DB
- 6379 : Redis

**Features utilisées** :
- "memory_store" : Après feature complexe (type + tags + relations)
- "task-master" : Tâches longues (get_tasks, rest_task, set_task_status)
- "sequential-thinking" : Problèmes complexes après échec

## 📚 MÉMOIRE (auto-stockage obligatoire)

**Au début sessions** :
- "memory_search" : Charger contexte
`;


const mockServers = [
  {
    id: '1',
    name: 'notion',
    package: 'npx',
    version: 'notion npx',
    status: 'configured' as const,
    chatEnabled: true
  },
  {
    id: '2',
    name: 'browserbase',
    package: 'npx',
    version: 'b55bc npx',
    status: 'configured' as const,
    chatEnabled: true
  },
  {
    id: '3',
    name: 'sentry',
    package: 'npx',
    version: 'sl8bc npx',
    status: 'configured' as const,
    chatEnabled: true
  },
  {
    id: '4',
    name: 'memory',
    package: 'python3',
    version: 'sl8bc python3',
    status: 'configured' as const,
    chatEnabled: true
  }
];

const mockSecrets = [
  {
    id: '1',
    name: 'OPENAI_API_KEY',
    value: 'sk-proj-***************************',
    description: 'OpenAI API key for GPT-4',
    createdAt: '2024-01-15T10:30:00Z',
    lastUsed: '2024-01-20T14:22:00Z'
  },
  {
    id: '2',
    name: 'ANTHROPIC_API_KEY',
    value: 'sk-ant-***************************',
    description: 'Anthropic API key for Claude',
    createdAt: '2024-01-10T09:15:00Z',
    lastUsed: '2024-01-21T11:45:00Z'
  },
  {
    id: '3',
    name: 'NEO4J_PASSWORD',
    value: '****************',
    description: 'Neo4j database password',
    createdAt: '2024-01-05T16:00:00Z',
    lastUsed: '2024-01-21T09:30:00Z'
  }
];

const mockLogs = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'info' as const,
    source: 'GraphQL',
    message: 'Query executed: memoryStats { qdrantVectors neo4jNodes }'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    level: 'success' as const,
    source: 'Memory',
    message: 'Successfully stored new memory: "React best practices"'
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 12000).toISOString(),
    level: 'warning' as const,
    source: 'Neo4j',
    message: 'Cache hit rate below 90%: current 87.3%'
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 23000).toISOString(),
    level: 'error' as const,
    source: 'Qdrant',
    message: 'Connection timeout: retrying in 5 seconds...'
  }
];

const automationRules = [
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Analyse et statistiques',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Génère un rapport de productivité',
      'Création de tâches / Je consulte ce mois ?',
      'Quel est mon temps moyen par tâche ?'
    ]
  },
  {
    id: 'create-memory',
    name: 'Create Memory',
    description: 'Stockage de mémoires et apprentissages',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Mémorise que je préfère React à Vue',
      'Note cette solution pour plus tard',
      'Retiens cette architecture'
    ]
  },
  {
    id: 'create-task',
    name: 'Create Task',
    description: 'Création de tâches depuis conversation',
    badge: 'Autonome',
    enabled: true,
    examples: [
      'Crée une tâche pour implémenter le login',
      'Ajoute ça à ma todo list'
    ]
  }
];

const levelIcons = {
  info: Info,
  warning: AlertCircle,
  error: XCircle,
  success: CheckCircle
};

const levelColors = {
  info: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  warning: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  error: 'bg-red-500/10 text-red-600 border-red-500/20',
  success: 'bg-green-500/10 text-green-600 border-green-500/20'
};

export function SystemSection() {
  const [currentPath, setCurrentPath] = useState('/home/zt1nkz/projects/BCI');
  const [terminalInput, setTerminalInput] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string[]>(['Welcome to Terminal Web', '$ ']);
  const [servers, setServers] = useState(mockServers);
  const [secrets, setSecrets] = useState(mockSecrets);
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>(mockFileContent);
  const [projectInstructions, setProjectInstructions] = useState('Explain how to use this codebase, what design patterns to follow, tech stack details, and any context that helps understand the project better. This content will be stored in the memory system for future reference.');

  const handleTerminalCommand = () => {
    if (!terminalInput.trim()) return;
    
    setTerminalOutput([...terminalOutput, `$ ${terminalInput}`, 'Command executed...']);
    setTerminalInput('');
  };

  const toggleSecretVisibility = (id: string) => {
    const newVisible = new Set(visibleSecrets);
    if (newVisible.has(id)) {
      newVisible.delete(id);
    } else {
      newVisible.add(id);
    }
    setVisibleSecrets(newVisible);
  };

  const filteredLogs = mockLogs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         log.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  const levelCounts = {
    info: mockLogs.filter(l => l.level === 'info').length,
    warning: mockLogs.filter(l => l.level === 'warning').length,
    error: mockLogs.filter(l => l.level === 'error').length,
    success: mockLogs.filter(l => l.level === 'success').length
  };

  return (
    <div className="space-y-6">
      <div>
        <h2>System</h2>
        <p className="text-muted-foreground">
          Infrastructure, Files, Terminal & Monitoring
        </p>
      </div>

      <Tabs defaultValue="files" className="w-full">
        <ScrollArea className="w-full">
          <TabsList className="inline-flex w-auto">
            <TabsTrigger value="files">
              <FolderOpen className="h-4 w-4 mr-2" />
              Files
            </TabsTrigger>
            <TabsTrigger value="terminal">
              <TerminalIcon className="h-4 w-4 mr-2" />
              Terminal
            </TabsTrigger>
            <TabsTrigger value="knowledge">
              <BookOpen className="h-4 w-4 mr-2" />
              Knowledge
            </TabsTrigger>
            <TabsTrigger value="rules">
              <Shield className="h-4 w-4 mr-2" />
              Rules
            </TabsTrigger>
            <TabsTrigger value="mcp">
              <Code2 className="h-4 w-4 mr-2" />
              MCP
            </TabsTrigger>
            <TabsTrigger value="secrets">
              <Key className="h-4 w-4 mr-2" />
              Secrets
            </TabsTrigger>
          </TabsList>
        </ScrollArea>

        {/* Files Tab */}
        <TabsContent value="files" className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setSelectedFile(null)}>
                <Home className="h-4 w-4 mr-2" />
                Home
              </Button>
              {selectedFile && (
                <Button variant="outline" size="sm">
                  <Save className="h-4 w-4 mr-2" />
                  Save
                </Button>
              )}
            </div>
            {selectedFile && (
              <Badge variant="secondary">Last saved: 16:13:27</Badge>
            )}
          </div>

          {selectedFile ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{selectedFile}</CardTitle>
                    <CardDescription className="font-mono text-xs">
                      {currentPath}/{selectedFile}
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4">
                  <div className="w-12 bg-muted/30 rounded-l-lg p-3 font-mono text-xs text-muted-foreground text-right select-none">
                    {Array.from({ length: fileContent.split('\n').length }, (_, i) => (
                      <div key={i}>{i + 1}</div>
                    ))}
                  </div>
                  <Textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    className="flex-1 font-mono text-sm min-h-[500px] border-0 focus-visible:ring-0 resize-none"
                  />
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>File Manager</CardTitle>
                  <Badge variant="secondary">Browse VPS Files</Badge>
                </div>
                <CardDescription className="font-mono text-xs">
                  {currentPath}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input placeholder="Search files..." className="pl-9" />
                </div>

                <ScrollArea className="h-[500px] pr-4">
                  <div className="space-y-1">
                    {mockFiles.map((file, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors cursor-pointer"
                        onClick={() => file.type === 'file' && setSelectedFile(file.name)}
                      >
                        {file.type === 'folder' ? (
                          <Folder className="h-5 w-5 text-blue-500" />
                        ) : (
                          <File className="h-5 w-5 text-muted-foreground" />
                        )}
                        <span className="flex-1 font-mono text-sm">{file.name}</span>
                        {file.type === 'file' && (
                          <Button variant="ghost" size="sm">Open</Button>
                        )}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Knowledge Tab */}
        <TabsContent value="knowledge" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3>Project Knowledge</h3>
              <p className="text-sm text-muted-foreground">
                Define project context and instructions for the memory system
              </p>
            </div>
            <Button>
              <Save className="h-4 w-4 mr-2" />
              Save project
            </Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Info className="h-5 w-5 text-blue-500" />
                <div>
                  <CardTitle>Project Instructions</CardTitle>
                  <CardDescription>
                    Explain how to use this codebase, what design patterns to follow, tech stack details, and any context that helps understand the project better. This content will be stored in the memory system for future reference.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                value={projectInstructions}
                onChange={(e) => setProjectInstructions(e.target.value)}
                placeholder="Enter project instructions, conventions, and documentation here..."
                className="min-h-[400px] font-mono text-sm"
              />
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Stored Contexts</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">3</div>
                <p className="text-xs text-muted-foreground mt-1">Project knowledge items</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Last Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl">Today</div>
                <p className="text-xs text-muted-foreground mt-1">16:13:27</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Auto-Sync</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Switch defaultChecked />
                  <span className="text-sm">Enabled</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Terminal Tab */}
        <TabsContent value="terminal" className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <TerminalIcon className="h-4 w-4 mr-2" />
                New Session
              </Button>
              <Button variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Clear
              </Button>
            </div>
            <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
              Connected
            </Badge>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Terminal Web</CardTitle>
              <CardDescription>Interactive SSH terminal with session management</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-black rounded-lg p-4 font-mono text-sm min-h-[400px] max-h-[600px] overflow-y-auto">
                <div className="text-green-400 space-y-1">
                  {terminalOutput.map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>
              </div>

              <div className="flex gap-2">
                <Input
                  placeholder="Enter command..."
                  value={terminalInput}
                  onChange={(e) => setTerminalInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleTerminalCommand()}
                  className="font-mono bg-black text-green-400 border-green-500/20"
                />
                <Button onClick={handleTerminalCommand}>Execute</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rules Tab */}
        <TabsContent value="rules" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>AI Automation Rules</CardTitle>
                  <CardDescription>
                    Configure what AI can do autonomously vs. with confirmation
                  </CardDescription>
                </div>
                <Badge variant="secondary">{automationRules.length} règles</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {automationRules.map((rule) => (
                  <AccordionItem key={rule.id} value={rule.id}>
                    <AccordionTrigger>
                      <div className="flex items-center justify-between w-full pr-4">
                        <div className="flex items-center gap-2">
                          <h4>{rule.name}</h4>
                          <Badge variant="outline" className="bg-chart-2/10 text-chart-2 border-chart-2/20">
                            {rule.badge}
                          </Badge>
                        </div>
                        <Switch 
                          defaultChecked={rule.enabled}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-3 pt-2">
                        <p className="text-sm text-muted-foreground">
                          {rule.description}
                        </p>
                        <div className="space-y-1.5">
                          <p className="text-sm text-muted-foreground">Exemples:</p>
                          <ul className="space-y-1">
                            {rule.examples.map((example, idx) => (
                              <li key={idx} className="text-sm text-foreground/80 pl-4 relative before:content-['•'] before:absolute before:left-0">
                                "{example}"
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        {/* MCP Tab */}
        <TabsContent value="mcp" className="space-y-6">
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm">
              <Heart className="h-4 w-4 mr-2" />
              Check Health
            </Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Install New MCP Server</CardTitle>
              <CardDescription>
                Enter npm package name or HTTP/HTTPS URL
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input placeholder="Package name or HTTP/HTTPS URL" className="flex-1" />
                <Button>Next</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Installed Servers ({servers.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-3">
                  {servers.map((server) => (
                    <div 
                      key={server.id}
                      className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center shrink-0">
                          <Settings className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="truncate">{server.name}</h4>
                            <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 shrink-0">
                              {server.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground truncate">{server.package}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3 shrink-0">
                        <Switch defaultChecked={server.chatEnabled} />
                        <Button variant="ghost" size="icon" className="text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Secrets Tab */}
        <TabsContent value="secrets" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Total Secrets</CardTitle>
                <Key className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{secrets.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Active</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{secrets.filter(s => s.lastUsed).length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Security</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl">AES-256</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Status</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge className="bg-green-500">Secure</Badge>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Encrypted Secrets</CardTitle>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Secret
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input placeholder="Search secrets..." className="pl-9" />
              </div>

              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-2">
                  {secrets.map((secret) => (
                    <div
                      key={secret.id}
                      className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <Key className="h-5 w-5 text-muted-foreground shrink-0" />
                        <div className="flex-1 min-w-0">
                          <h4 className="truncate">{secret.name}</h4>
                          <p className="text-sm text-muted-foreground truncate">
                            {secret.description}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => toggleSecretVisibility(secret.id)}
                        >
                          {visibleSecrets.has(secret.id) ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Info</CardTitle>
                <Info className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{levelCounts.info}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Warnings</CardTitle>
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{levelCounts.warning}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Errors</CardTitle>
                <XCircle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{levelCounts.error}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">Success</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl">{levelCounts.success}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>System Logs</CardTitle>
                <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                  Live
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search logs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={levelFilter} onValueChange={setLevelFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1 font-mono text-sm max-h-[400px] overflow-y-auto bg-muted/30 rounded-lg p-4">
                {filteredLogs.map((log) => {
                  const Icon = levelIcons[log.level];
                  return (
                    <div key={log.id} className="flex items-start gap-3 py-2 border-b border-border/50 last:border-0">
                      <Icon className="h-4 w-4 mt-0.5 shrink-0" style={{
                        color: log.level === 'info' ? '#3b82f6' :
                               log.level === 'warning' ? '#eab308' :
                               log.level === 'error' ? '#ef4444' :
                               '#22c55e'
                      }} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          <Badge variant="outline" className={levelColors[log.level]}>
                            {log.level.toUpperCase()}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {log.source}
                          </Badge>
                        </div>
                        <p className="text-foreground break-words">{log.message}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
