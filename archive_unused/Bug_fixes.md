2025-08-11T16:51:13.418910-07:00
pnpm run buildCommand exit with code 1

> react-template@0.0.0 build /workspace/dashboard
> vite build

vite v5.4.19 building for production...
transforming...
✓ 25 modules transformed.
x Build failed in 1.73s
error during build:
[vite]: Rollup failed to resolve import "date-fns" from "/workspace/dashboard/src/components/TradingChart.jsx".
This is most likely unintended because it can break your application at runtime.
If you do want to externalize this module explicitly add it to
`build.rollupOptions.external`
    at viteWarn (file:///workspace/dashboard/node_modules/.pnpm/vite@5.4.19_@types+node@24.2.1_terser@5.43.1/node_modules/vite/dist/node/chunks/dep-C6uTJdX2.js:65839:17)
    at onwarn (file:///workspace/dashboard/node_modules/.pnpm/@vitejs+plugin-react@4.7.0_vite@5.4.19_@types+node@24.2.1_terser@5.43.1_/node_modules/@vitejs/plugin-react/dist/index.js:90:7)
    at onRollupWarning (file:///workspace/dashboard/node_modules/.pnpm/vite@5.4.19_@types+node@24.2.1_terser@5.43.1/node_modules/vite/dist/node/chunks/dep-C6uTJdX2.js:65869:5)
    at onwarn (file:///workspace/dashboard/node_modules/.pnpm/vite@5.4.19_@types+node@24.2.1_terser@5.43.1/node_modules/vite/dist/node/chunks/dep-C6uTJdX2.js:65534:7)
    at file:///workspace/dashboard/node_modules/.pnpm/rollup@4.46.2/node_modules/rollup/dist/es/shared/node-entry.js:20880:13
    at Object.logger [as onLog] (file:///workspace/dashboard/node_modules/.pnpm/rollup@4.46.2/node_modules/rollup/dist/es/shared/node-entry.js:22748:9)
    at ModuleLoader.handleInvalidResolvedId (file:///workspace/dashboard/node_modules/.pnpm/rollup@4.46.2/node_modules/rollup/dist/es/shared/node-entry.js:21492:26)
    at file:///workspace/dashboard/node_modules/.pnpm/rollup@4.46.2/node_modules/rollup/dist/es/shared/node-entry.js:21450:26
 ELIFECYCLE  Command failed with exit code 1.