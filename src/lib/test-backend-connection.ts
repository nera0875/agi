/**
 * Utility functions for testing backend connection
 * Use these functions to diagnose connection issues
 */

import { graphqlEndpoint } from '../config/api';

interface ConnectionTestResult {
  endpoint: string;
  connected: boolean;
  statusCode?: number;
  responseTime?: number;
  error?: string;
  timestamp: Date;
}

/**
 * Test basic HTTP connectivity to the GraphQL endpoint
 */
export async function testHttpConnection(): Promise<ConnectionTestResult> {
  const startTime = Date.now();

  try {
    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: '{ __typename }',
      }),
      signal: AbortSignal.timeout(5000),
    });

    const responseTime = Date.now() - startTime;

    return {
      endpoint: graphqlEndpoint,
      connected: response.ok,
      statusCode: response.status,
      responseTime,
      timestamp: new Date(),
    };
  } catch (error) {
    const responseTime = Date.now() - startTime;
    const errorMsg =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      endpoint: graphqlEndpoint,
      connected: false,
      responseTime,
      error: errorMsg,
      timestamp: new Date(),
    };
  }
}

/**
 * Test GraphQL health check query
 */
export async function testGraphQLHealthCheck(): Promise<ConnectionTestResult> {
  const startTime = Date.now();

  try {
    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `
          query {
            healthCheck {
              service
              status
              message
            }
          }
        `,
      }),
      signal: AbortSignal.timeout(5000),
    });

    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      return {
        endpoint: graphqlEndpoint,
        connected: false,
        statusCode: response.status,
        responseTime,
        error: `HTTP ${response.status}`,
        timestamp: new Date(),
      };
    }

    const payload = await response.json();

    if (payload.errors && payload.errors.length > 0) {
      return {
        endpoint: graphqlEndpoint,
        connected: false,
        statusCode: 200,
        responseTime,
        error: `GraphQL error: ${payload.errors[0].message}`,
        timestamp: new Date(),
      };
    }

    return {
      endpoint: graphqlEndpoint,
      connected: true,
      statusCode: 200,
      responseTime,
      timestamp: new Date(),
    };
  } catch (error) {
    const responseTime = Date.now() - startTime;
    const errorMsg =
      error instanceof Error ? error.message : 'Unknown error occurred';

    return {
      endpoint: graphqlEndpoint,
      connected: false,
      responseTime,
      error: errorMsg,
      timestamp: new Date(),
    };
  }
}

/**
 * Run comprehensive connection test
 */
export async function runFullConnectionTest() {
  console.log('=== Backend Connection Test ===');
  console.log(`Testing endpoint: ${graphqlEndpoint}`);
  console.log('');

  // Test 1: HTTP connectivity
  console.log('Test 1: HTTP Connectivity');
  const httpTest = await testHttpConnection();
  console.table(httpTest);

  // Test 2: GraphQL health check
  console.log('\nTest 2: GraphQL Health Check');
  const graphqlTest = await testGraphQLHealthCheck();
  console.table(graphqlTest);

  // Summary
  console.log('\n=== Summary ===');
  const allConnected = httpTest.connected && graphqlTest.connected;
  console.log(
    `Backend Status: ${allConnected ? '✅ CONNECTED' : '❌ DISCONNECTED'}`
  );

  if (httpTest.error) {
    console.warn(`HTTP Error: ${httpTest.error}`);
  }
  if (graphqlTest.error) {
    console.warn(`GraphQL Error: ${graphqlTest.error}`);
  }

  if (httpTest.responseTime) {
    console.log(`Average Response Time: ${httpTest.responseTime}ms`);
  }

  return { httpTest, graphqlTest, allConnected };
}

/**
 * Diagnose common connection issues
 */
export function diagnoseConnectionIssue(error: string): string {
  if (error.includes('ERR_CONNECTION_REFUSED')) {
    return 'Backend server is not running on port 8000. Start the backend with: python -m backend.main';
  }
  if (error.includes('ENOTFOUND')) {
    return 'DNS resolution failed. Check the backend hostname/IP address.';
  }
  if (error.includes('timeout')) {
    return 'Request timeout. Backend may be slow or unresponsive. Check backend logs.';
  }
  if (error.includes('CORS')) {
    return 'CORS error. Backend CORS configuration may be incorrect.';
  }
  if (error.includes('404')) {
    return 'GraphQL endpoint not found. Verify endpoint URL is correct.';
  }
  if (error.includes('500')) {
    return 'Backend server error. Check backend logs for details.';
  }
  return `Unknown error: ${error}`;
}
