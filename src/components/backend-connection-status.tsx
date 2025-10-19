import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, WifiOff } from 'lucide-react';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import { graphqlEndpoint } from '../config/api';

type ConnectionStatus = 'checking' | 'connected' | 'offline';

interface BackendConnectionStatusProps {
  onStatusChange?: (status: ConnectionStatus) => void;
}

export function BackendConnectionStatus({ onStatusChange }: BackendConnectionStatusProps) {
  const [status, setStatus] = useState<ConnectionStatus>('checking');
  const [lastCheckTime, setLastCheckTime] = useState<Date | null>(null);
  const [hasShownOfflineNotice, setHasShownOfflineNotice] = useState(false);

  useEffect(() => {
    // Check backend connectivity
    const checkBackendConnection = async () => {
      try {
        const startTime = Date.now();
        const response = await fetch(graphqlEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: '{ healthCheck { service status } }',
          }),
          signal: AbortSignal.timeout(5000), // 5s timeout
        });

        const elapsed = Date.now() - startTime;

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json();
        if (payload.errors && payload.errors.length > 0) {
          throw new Error(payload.errors[0]?.message ?? 'GraphQL error');
        }

        // Connected successfully
        setStatus('connected');
        setLastCheckTime(new Date());
        setHasShownOfflineNotice(false);

        console.log(
          `✅ Backend connected (${graphqlEndpoint}) - Response time: ${elapsed}ms`
        );
      } catch (error) {
        // Handle different types of errors
        const errorMsg =
          error instanceof Error ? error.message : 'Connection failed';

        setStatus('offline');
        setLastCheckTime(new Date());

        // Show offline notice only once per session
        if (!hasShownOfflineNotice) {
          console.warn(
            `🔌 Backend offline (${graphqlEndpoint}) - ${errorMsg}`
          );
          toast.info('Backend déconnecté - Mode démo activé', {
            description: 'Les données seront chargées depuis le cache local',
            duration: 3000,
            position: 'bottom-right',
          });
          setHasShownOfflineNotice(true);
        }
      }
    };

    // Initial check
    checkBackendConnection();

    // Poll every 30 seconds
    const interval = setInterval(checkBackendConnection, 30000);

    // Listen for Apollo network errors (real-time detection)
    const handleApolloNetworkError = () => {
      setStatus('offline');
      setLastCheckTime(new Date());
      if (!hasShownOfflineNotice) {
        console.warn('🔌 Backend connection lost (via Apollo)');
        setHasShownOfflineNotice(true);
      }
    };

    window.addEventListener('apollo-network-error', handleApolloNetworkError);

    return () => {
      clearInterval(interval);
      window.removeEventListener('apollo-network-error', handleApolloNetworkError);
    };
  }, [hasShownOfflineNotice]);

  // Notify parent component of status changes
  useEffect(() => {
    onStatusChange?.(status);
  }, [status, onStatusChange]);

  // Render badge based on status
  const getStatusDisplay = () => {
    switch (status) {
      case 'checking':
        return (
          <Badge variant="outline" className="animate-pulse">
            Vérification...
          </Badge>
        );
      case 'connected':
        return (
          <Badge variant="outline" className="flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3 text-foreground" />
            Connecté
          </Badge>
        );
      case 'offline':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <WifiOff className="h-3 w-3" />
            Déconnecté
          </Badge>
        );
    }
  };

  return (
    <div className="flex items-center gap-2">
      {getStatusDisplay()}
      {lastCheckTime && (
        <span className="text-xs text-muted-foreground">
          {lastCheckTime.toLocaleTimeString('fr-FR')}
        </span>
      )}
    </div>
  );
}
