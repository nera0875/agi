/**
 * Centralized API configuration
 * All API endpoints are defined here for easy maintenance
 */

// Détecter l'URL du serveur basée sur le host actuel
const getServerUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000';

  const currentHost = window.location.hostname;
  const protocol = window.location.protocol;

  // En production sur Vercel, utiliser neurodopa.fr
  if (currentHost.includes('vercel.app')) {
    return 'https://neurodopa.fr/api';
  }

  // Si accédé via domaine HTTPS, utiliser HTTPS
  if (protocol === 'https:' && currentHost !== 'localhost') {
    return `https://${currentHost}/api`;
  }

  // Développement local
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    return `http://${currentHost}:8000`;
  }

  // Default: utiliser le même protocole et host
  return `${protocol}//${currentHost}:8000`;
};

export const API_CONFIG = {
  /**
   * GraphQL endpoint exposed par le backend AGI.
   * Override possible via VITE_GRAPHQL_ENDPOINT.
   */
  graphqlEndpoint:
    import.meta.env.VITE_GRAPHQL_ENDPOINT || getServerUrl() + "/graphql",

  /**
   * WebSocket endpoint pour les subscriptions GraphQL.
   * Override possible via VITE_GRAPHQL_WS_ENDPOINT.
   */
  wsEndpoint:
    import.meta.env.VITE_GRAPHQL_WS_ENDPOINT || getServerUrl().replace('https', 'wss').replace('http', 'ws') + "/graphql",
} as const;

// Export individual endpoints for convenience
export const { graphqlEndpoint, wsEndpoint } = API_CONFIG;
