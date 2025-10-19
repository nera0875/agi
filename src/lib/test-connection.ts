/**
 * Simple Connection Test
 * Can be used from CLI for quick validation
 */

import { graphqlEndpoint } from '../config/api';

export async function testConnection(): Promise<boolean> {
  try {
    console.log('Testing GraphQL connection...');
    console.log(`Endpoint: ${graphqlEndpoint}`);

    const response = await fetch(graphqlEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      mode: 'cors',
      credentials: 'omit',
      body: JSON.stringify({
        query: '{ healthCheck { service status } }',
      }),
    });

    if (!response.ok) {
      console.error(`HTTP ${response.status}`);
      return false;
    }

    const data = await response.json();
    if (data.errors) {
      console.error('GraphQL error:', data.errors[0]?.message);
      return false;
    }

    console.log('✅ Connection successful!');
    console.log('Health status:', data.data?.healthCheck);
    return true;
  } catch (error) {
    console.error('Connection failed:', error instanceof Error ? error.message : error);
    return false;
  }
}

// Export for testing
if (import.meta.env.DEV) {
  (window as any).__testConnection = testConnection;
}
