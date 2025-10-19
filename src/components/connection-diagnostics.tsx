import { useState } from 'react';
import { Activity, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import {
  testHttpConnection,
  testGraphQLHealthCheck,
  diagnoseConnectionIssue,
} from '../lib/test-backend-connection';

interface TestLog {
  id: string;
  timestamp: Date;
  test: string;
  status: 'running' | 'success' | 'error';
  message: string;
  details?: Record<string, any>;
}

export function ConnectionDiagnostics() {
  const [logs, setLogs] = useState<TestLog[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const addLog = (
    test: string,
    status: 'running' | 'success' | 'error',
    message: string,
    details?: Record<string, any>
  ) => {
    const log: TestLog = {
      id: Math.random().toString(36).substring(2, 11),
      timestamp: new Date(),
      test,
      status,
      message,
      details,
    };
    setLogs((prev) => [log, ...prev]);
  };

  const runDiagnostics = async () => {
    setIsRunning(true);
    setLogs([]);

    try {
      // Test 1: HTTP Connectivity
      addLog('HTTP Connection', 'running', 'Testing HTTP connectivity...');
      const httpResult = await testHttpConnection();
      addLog(
        'HTTP Connection',
        httpResult.connected ? 'success' : 'error',
        httpResult.connected ? 'HTTP connection successful' : 'HTTP connection failed',
        httpResult
      );

      if (!httpResult.connected) {
        const diagnosis = diagnoseConnectionIssue(httpResult.error || '');
        addLog('Diagnosis', 'error', diagnosis, { error: httpResult.error });
      }

      // Test 2: GraphQL Health Check
      addLog(
        'GraphQL Health Check',
        'running',
        'Testing GraphQL endpoint...'
      );
      const graphqlResult = await testGraphQLHealthCheck();
      addLog(
        'GraphQL Health Check',
        graphqlResult.connected ? 'success' : 'error',
        graphqlResult.connected
          ? `GraphQL health check successful (${graphqlResult.responseTime}ms)`
          : 'GraphQL health check failed',
        graphqlResult
      );

      if (!graphqlResult.connected) {
        const diagnosis = diagnoseConnectionIssue(graphqlResult.error || '');
        addLog('Diagnosis', 'error', diagnosis, { error: graphqlResult.error });
      }

      // Summary
      const allPassed = httpResult.connected && graphqlResult.connected;
      toast[allPassed ? 'success' : 'error'](
        allPassed ? 'All tests passed!' : 'Some tests failed'
      );
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      addLog('Test Error', 'error', errorMsg);
      toast.error('Diagnostic test failed');
    } finally {
      setIsRunning(false);
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="space-y-4">
      <Card className="border-border bg-card">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Connection Diagnostics
          </CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={runDiagnostics}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Run Tests
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearLogs}
              disabled={logs.length === 0}
            >
              Clear
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {logs.length === 0 ? (
            <p className="text-muted-foreground text-sm text-center py-4">
              Click "Run Tests" to diagnose backend connection
            </p>
          ) : (
            <ScrollArea className="h-96 rounded border border-border bg-muted p-3">
              <div className="space-y-2">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    className="rounded border border-border bg-card p-3 space-y-2 hover:bg-accent transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 flex-1">
                        {log.status === 'running' && (
                          <Loader2 className="h-4 w-4 animate-spin text-foreground" />
                        )}
                        {log.status === 'success' && (
                          <CheckCircle2 className="h-4 w-4 text-foreground" />
                        )}
                        {log.status === 'error' && (
                          <AlertCircle className="h-4 w-4 text-foreground" />
                        )}
                        <div>
                          <p className="text-foreground text-sm font-medium">
                            {log.test}
                          </p>
                          <p className="text-muted-foreground text-xs">
                            {log.message}
                          </p>
                        </div>
                      </div>
                      <Badge
                        variant={
                          log.status === 'success' ? 'outline' : 'destructive'
                        }
                        className="text-xs"
                      >
                        {log.status === 'running' ? 'Running' : log.status}
                      </Badge>
                    </div>
                    {log.details && (
                      <details className="text-xs">
                        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                          Show details
                        </summary>
                        <pre className="mt-2 rounded bg-muted p-2 overflow-x-auto text-xs text-muted-foreground">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      <div className="text-xs text-muted-foreground space-y-1">
        <p>
          Use this tool to test the backend GraphQL connection and diagnose
          issues.
        </p>
        <p>
          Common issues:
        </p>
        <ul className="list-disc list-inside space-y-1 ml-2">
          <li>Backend server not running on port 8000</li>
          <li>Network connectivity issues</li>
          <li>CORS configuration problems</li>
          <li>GraphQL endpoint incorrect</li>
        </ul>
      </div>
    </div>
  );
}
