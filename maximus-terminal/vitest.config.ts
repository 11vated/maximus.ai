/// <reference types="vitest" />
import type { Config } from 'vitest';

export default {
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/tests/*.test.{ts,tsx}'],
  },
} satisfies Config;
