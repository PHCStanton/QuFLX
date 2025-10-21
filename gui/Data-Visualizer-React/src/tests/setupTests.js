import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Map jest globals to vitest for compatibility in existing tests
// This allows using jest.fn(), jest.mock(), etc. in vitest
// while we gradually migrate tests.
// eslint-disable-next-line no-undef
globalThis.jest = vi;

// JSDOM matchMedia mock to satisfy libraries (e.g., MUI) that query it
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Clean up after each test
afterEach(() => {
  cleanup();
});