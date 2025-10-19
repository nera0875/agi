import { ApolloClient, InMemoryCache, HttpLink, from } from '@apollo/client/core';
import { onError } from '@apollo/client/link/error';
import { RetryLink } from '@apollo/client/link/retry';
import { graphqlEndpoint } from '../config/api';

// Utiliser la config centralisée au lieu de hardcoder
const getGraphqlEndpoint = () => {
  console.log(`🔌 GraphQL Endpoint: ${graphqlEndpoint}`);
  return graphqlEndpoint;
};

// Retry link with exponential backoff
const retryLink = new RetryLink({
  delay: {
    initial: 300,
    max: 30000,
    jitter: true,
  },
  attempts: {
    max: 3,
    retryIf: (error, _operation) => {
      // Don't retry on CORS or connection refused errors
      if (error?.message?.includes('ERR_CONNECTION_REFUSED')) {
        console.warn('Backend connection refused - not retrying');
        return false;
      }
      if (error?.message?.includes('ERR_INTERNET_DISCONNECTED')) {
        return false;
      }
      if (error?.message?.includes('Failed to fetch')) {
        // Retry network failures
        return true;
      }
      // Retry on network errors or 5xx errors
      return !!error && (
        error.message.includes('NetworkError') ||
        error.message.includes('fetch') ||
        error.message.includes('timeout') ||
        (error.statusCode && error.statusCode >= 500)
      );
    },
  },
});

// Error handling link with Sentry
const errorLink = onError(({ graphQLErrors, networkError, operation }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path }) => {
      console.error(
        `[GraphQL error]: Message: ${message}, Location: ${JSON.stringify(locations)}, Path: ${path}`
      );

      // Send GraphQL errors to Sentry
      try {
        const { captureException } = require('./sentry');
        captureException(new Error(`GraphQL Error: ${message}`), {
          operation: operation.operationName,
          path,
          locations,
          query: operation.query.loc?.source.body.substring(0, 200), // First 200 chars
        });
      } catch (e) {
        // Sentry not available
      }
    });
  }

  if (networkError) {
    const isBackendOffline =
      networkError.message?.includes('ERR_CONNECTION_REFUSED') ||
      networkError.message?.includes('fetch failed') ||
      networkError.message?.includes('Network request failed');

    const severity = isBackendOffline ? 'warn' : 'error';
    console[severity](
      `[Network error ${operation.operationName}]: ${networkError.message}`
    );

    // Emit custom event for health check to detect backend offline
    window.dispatchEvent(
      new CustomEvent('apollo-network-error', {
        detail: {
          operation: operation.operationName,
          error: networkError.message,
          isBackendOffline,
        },
      })
    );

    // Send critical network errors to Sentry (not backend offline)
    if (!isBackendOffline) {
      try {
        const { captureException } = require('./sentry');
        captureException(networkError, {
          operation: operation.operationName,
          type: 'network_error',
          endpoint: getGraphqlEndpoint(),
        });
      } catch (e) {
        // Sentry not available
      }
    }
  }
});

// HTTP link with CORS - URI DYNAMIQUE (fonction appelée à chaque requête)
const httpLink = new HttpLink({
  uri: getGraphqlEndpoint, // FONCTION, pas string !
  credentials: 'omit',
  fetchOptions: {
    mode: 'cors',
    // Add timeout via AbortSignal (5 seconds)
    timeout: 5000,
  },
  // Custom fetch with timeout support
  fetch: async (uri, options) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch(uri, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(
          'GraphQL request timeout after 5 seconds - Backend may be unreachable'
        );
      }
      throw error;
    }
  },
});

// Combine links: error handling → retry → http
const link = from([errorLink, retryLink, httpLink]);

// Apollo Client with normalized cache
export const apolloClient = new ApolloClient({
  link,
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          databaseNodes: {
            merge(existing = [], incoming) {
              return incoming;
            },
          },
          systemStatus: {
            merge(existing, incoming) {
              return incoming;
            },
          },
        },
      },
      DatabaseNode: {
        keyFields: ['id'],
      },
      Memory: {
        keyFields: ['id'],
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
      notifyOnNetworkStatusChange: true,
    },
    query: {
      fetchPolicy: 'network-only',
      errorPolicy: 'all',
    },
    mutate: {
      errorPolicy: 'all',
    },
  },
  connectToDevTools: import.meta.env.DEV,
});
