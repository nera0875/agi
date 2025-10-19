/**
 * Connection Diagnostics - Debug Apollo Client connection issues
 * This utility provides detailed debugging information about backend connectivity
 */

import { graphqlEndpoint } from '../config/api';

interface DiagnosticResult {
  timestamp: string;
  endpoint: string;
  healthCheckResult: {
    success: boolean;
    statusCode?: number;
    error?: string;
    duration?: number;
  };
  introspectionResult: {
    success: boolean;
    statusCode?: number;
    error?: string;
    duration?: number;
  };
  corsHeaders?: Record<string, string>;
}

export async function runConnectionDiagnostics(): Promise<DiagnosticResult> {
  const result: DiagnosticResult = {
    timestamp: new Date().toISOString(),
    endpoint: graphqlEndpoint,
    healthCheckResult: { success: false },
    introspectionResult: { success: false },
  };

  console.group('[Diagnostics] Backend Connection Check');
  console.log(`Endpoint: ${graphqlEndpoint}`);

  // Test 1: Simple health check
  console.log('[Diagnostics] Test 1: Health check query...');
  const healthStart = performance.now();
  try {
    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors',
      credentials: 'omit',
      body: JSON.stringify({
        query: '{ healthCheck { service status } }',
      }),
    });

    const duration = performance.now() - healthStart;
    result.healthCheckResult.statusCode = response.status;
    result.healthCheckResult.duration = duration;

    // Capture CORS headers
    const corsHeaders: Record<string, string> = {};
    ['access-control-allow-origin', 'access-control-allow-methods', 'access-control-allow-headers'].forEach(header => {
      const value = response.headers.get(header);
      if (value) corsHeaders[header] = value;
    });
    if (Object.keys(corsHeaders).length > 0) {
      result.corsHeaders = corsHeaders;
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data.errors) {
      throw new Error(data.errors[0]?.message || 'GraphQL error');
    }

    result.healthCheckResult.success = true;
    console.log(`✅ Health check passed (${duration.toFixed(0)}ms)`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    result.healthCheckResult.error = errorMessage;
    console.error(`❌ Health check failed: ${errorMessage}`);
  }

  // Test 2: Introspection query (full schema)
  console.log('[Diagnostics] Test 2: Introspection query...');
  const introspectionStart = performance.now();
  try {
    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors',
      credentials: 'omit',
      body: JSON.stringify({
        query: `
          query IntrospectionQuery {
            __schema {
              types {
                name
              }
            }
          }
        `,
      }),
    });

    const duration = performance.now() - introspectionStart;
    result.introspectionResult.statusCode = response.status;
    result.introspectionResult.duration = duration;

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    if (data.errors) {
      throw new Error(data.errors[0]?.message || 'GraphQL error');
    }

    result.introspectionResult.success = true;
    console.log(`✅ Introspection passed (${duration.toFixed(0)}ms), ${data.data?.__schema?.types?.length} types`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    result.introspectionResult.error = errorMessage;
    console.error(`❌ Introspection failed: ${errorMessage}`);
  }

  // Summary
  const isConnected = result.healthCheckResult.success && result.introspectionResult.success;
  if (isConnected) {
    console.log('✅ Backend connection: HEALTHY');
  } else {
    console.warn('⚠️ Backend connection: DEGRADED OR OFFLINE');
  }

  console.groupEnd();
  return result;
}

// Auto-run diagnostics on page load if in development
if (import.meta.env.DEV) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      console.info('[Diagnostics] Automatic connection check enabled in dev mode');
      runConnectionDiagnostics().catch(console.error);
    }, 1000);
  });

  // Expose diagnostics function globally for manual testing
  (window as any).__runDiagnostics = runConnectionDiagnostics;
  console.log('💡 Run __runDiagnostics() in console to test connection');
}
