// Lightweight debug logger with level control via Vite env or localStorage
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3, trace: 4 };

function normalizeLevel(level) {
  if (!level) return null;
  const l = String(level).toLowerCase().trim();
  if (l in LEVELS) return l;
  // allow numeric levels
  if (!Number.isNaN(Number(l))) {
    const entries = Object.entries(LEVELS);
    const match = entries.find(([, val]) => val === Number(l));
    return match ? match[0] : null;
  }
  return null;
}

let currentLevel = normalizeLevel(
  (import.meta?.env && import.meta.env.VITE_LOG_LEVEL) ||
  (import.meta?.env && (import.meta.env.DEV ? 'debug' : 'warn')) ||
  undefined
) || 'warn';

try {
  const stored = normalizeLevel(localStorage.getItem('LOG_LEVEL'));
  if (stored) currentLevel = stored;
} catch {}

export function setLogLevel(level) {
  const norm = normalizeLevel(level);
  if (norm) {
    currentLevel = norm;
    try { localStorage.setItem('LOG_LEVEL', norm); } catch {}
  }
}

export function getLogLevel() {
  return currentLevel;
}

function shouldLog(level) {
  return LEVELS[level] <= LEVELS[currentLevel];
}

export function createLogger(namespace = 'app') {
  const prefix = `[${namespace}]`;
  return {
    error: (...args) => shouldLog('error') && console.error(prefix, ...args),
    warn:  (...args) => shouldLog('warn')  && console.warn(prefix, ...args),
    info:  (...args) => shouldLog('info')  && console.info(prefix, ...args),
    debug: (...args) => shouldLog('debug') && console.debug(prefix, ...args),
    trace: (...args) => shouldLog('trace') && console.trace(prefix, ...args),
  };
}

export const logger = createLogger('app');