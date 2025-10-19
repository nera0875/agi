import { useState, useEffect } from 'react';

/**
 * Hook to detect if backend is available
 * Falls back to mock mode if backend is unreachable
 */
export function useMockMode() {
  const [isMockMode, setIsMockMode] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        // Try to reach backend health endpoint (match current hostname)
        const backendUrl = typeof window !== 'undefined'
          ? `http://${window.location.hostname}:8000/health`
          : 'http://localhost:8001/health';
        const response = await fetch(backendUrl, {
          method: 'GET',
          signal: AbortSignal.timeout(2000), // 2s timeout
        });

        if (response.ok) {
          setIsMockMode(false);
        } else {
          setIsMockMode(true);
        }
      } catch (error) {
        // Backend unreachable - use mock mode
        console.warn('Backend unreachable, using mock mode');
        setIsMockMode(true);
      } finally {
        setIsChecking(false);
      }
    };

    checkBackend();
  }, []);

  return { isMockMode, isChecking };
}
