import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { 
  RefreshCw, 
  Download, 
  Trash2, 
  Search,
  AlertCircle,
  Info,
  CheckCircle,
  XCircle
} from "lucide-react";
import { useState } from "react";

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  source: string;
  message: string;
}

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date().toISOString(),
    level: 'info',
    source: 'GraphQL',
    message: 'Query executed: memoryStats { qdrantVectors neo4jNodes }'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    level: 'success',
    source: 'Memory',
    message: 'Successfully stored new memory: "React best practices"'
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 12000).toISOString(),
    level: 'warning',
    source: 'Neo4j',
    message: 'Cache hit rate below 90%: current 87.3%'
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 23000).toISOString(),
    level: 'info',
    source: 'Tasks',
    message: 'Task updated: "Implement GraphQL API" → status: in-progress'
  },
  {
    id: '5',
    timestamp: new Date(Date.now() - 45000).toISOString(),
    level: 'error',
    source: 'Qdrant',
    message: 'Connection timeout: retrying in 5 seconds...'
  },
  {
    id: '6',
    timestamp: new Date(Date.now() - 67000).toISOString(),
    level: 'success',
    source: 'MCP',
    message: 'MCP server "notion" initialized successfully'
  },
  {
    id: '7',
    timestamp: new Date(Date.now() - 89000).toISOString(),
    level: 'info',
    source: 'API',
    message: 'Health check passed: all services operational'
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

export function LogsSection() {
  const [logs, setLogs] = useState<LogEntry[]>(mockLogs);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         log.source.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    const matchesSource = sourceFilter === 'all' || log.source === sourceFilter;
    return matchesSearch && matchesLevel && matchesSource;
  });

  const sources = Array.from(new Set(logs.map(log => log.source)));

  const levelCounts = {
    info: logs.filter(l => l.level === 'info').length,
    warning: logs.filter(l => l.level === 'warning').length,
    error: logs.filter(l => l.level === 'error').length,
    success: logs.filter(l => l.level === 'success').length
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>Logs</h2>
          <p className="text-muted-foreground">
            Real-time system logs and monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm">
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

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
            <div>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>Real-time streaming logs from all services</CardDescription>
            </div>
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
            <Select value={sourceFilter} onValueChange={setSourceFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {sources.map(source => (
                  <SelectItem key={source} value={source}>{source}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1 font-mono text-sm max-h-[600px] overflow-y-auto bg-muted/30 rounded-lg p-4">
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
    </div>
  );
}
