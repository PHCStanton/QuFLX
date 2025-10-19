/**
 * Detect the backend API base URL based on the environment
 * In Replit/production: uses current origin (Vite proxy handles routing)
 * In local dev: uses explicit backend port
 */
export const detectBackendUrl = () => {
  try {
    const { protocol, hostname } = window.location;
    
    const envUrl = import.meta?.env?.VITE_API_URL;
    if (envUrl) return envUrl;
    
    const isReplit = hostname.includes('replit.dev') || hostname.includes('repl.co');
    if (isReplit) {
      return `${protocol}//${hostname}`;
    }
    
    return `${protocol}//${hostname}:3001`;
  } catch {
    return 'http://localhost:3001';
  }
};

/**
 * Detect the WebSocket server URL based on the environment
 * Note: Socket.IO uses HTTP/HTTPS protocol for initial connection,
 * then upgrades to WebSocket internally
 */
export const detectSocketUrl = () => {
  try {
    const { protocol, hostname } = window.location;
    
    const envUrl = import.meta?.env?.VITE_SOCKET_URL;
    if (envUrl) return envUrl;
    
    return `${protocol}//${hostname}${window?.location?.port ? ':' + window?.location?.port : ''}`;
  } catch {
    return 'http://localhost:5000';
  }
};
