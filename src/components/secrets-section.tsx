import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { 
  Plus, 
  Search, 
  RefreshCw, 
  Eye, 
  EyeOff, 
  Copy, 
  Trash2,
  Key
} from "lucide-react";
import { useState } from "react";

interface Secret {
  id: string;
  name: string;
  value: string;
  description: string;
  createdAt: string;
  lastUsed?: string;
}

const mockSecrets: Secret[] = [
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
  },
  {
    id: '4',
    name: 'QDRANT_API_KEY',
    value: '****************',
    description: 'Qdrant vector database API key',
    createdAt: '2024-01-08T12:20:00Z'
  }
];

export function SecretsSection() {
  const [secrets, setSecrets] = useState<Secret[]>(mockSecrets);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());

  const toggleSecretVisibility = (id: string) => {
    const newVisible = new Set(visibleSecrets);
    if (newVisible.has(id)) {
      newVisible.delete(id);
    } else {
      newVisible.add(id);
    }
    setVisibleSecrets(newVisible);
  };

  const copyToClipboard = (value: string) => {
    navigator.clipboard.writeText(value);
  };

  const deleteSecret = (id: string) => {
    setSecrets(secrets.filter(s => s.id !== id));
  };

  const filteredSecrets = secrets.filter(secret =>
    secret.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    secret.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2>Secrets</h2>
          <p className="text-muted-foreground">
            Manage encrypted API keys and sensitive data
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Secret
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Total Secrets</CardTitle>
            <Key className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl">{secrets.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Encrypted</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl">{secrets.filter(s => s.lastUsed).length}</div>
            <p className="text-xs text-muted-foreground mt-1">Recently used</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Security</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl">AES-256</div>
            <p className="text-xs text-muted-foreground mt-1">Encryption</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge className="bg-green-500">Secure</Badge>
            <p className="text-xs text-muted-foreground mt-1">All encrypted</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Encrypted Secrets</CardTitle>
              <CardDescription>API keys, passwords, and sensitive configuration</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search secrets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <div className="space-y-2">
            {filteredSecrets.map((secret) => (
              <div
                key={secret.id}
                className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                    <Key className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="truncate">{secret.name}</h4>
                      {secret.lastUsed && (
                        <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                          Active
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate">
                      {secret.description}
                    </p>
                    <div className="flex items-center gap-4 mt-1">
                      <span className="text-xs text-muted-foreground font-mono">
                        {visibleSecrets.has(secret.id) ? secret.value : secret.value}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Created: {new Date(secret.createdAt).toLocaleDateString()}
                      </span>
                      {secret.lastUsed && (
                        <span className="text-xs text-muted-foreground">
                          Last used: {new Date(secret.lastUsed).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
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
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => copyToClipboard(secret.value)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteSecret(secret.id)}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              🔒 All secrets are encrypted using AES-256 encryption before storage
            </p>
            <p className="text-muted-foreground">
              🔑 Secrets are only decrypted in memory when actively used
            </p>
            <p className="text-muted-foreground">
              ⚠️ Never share or expose your API keys. Rotate them regularly.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
