## Agent skills

### Issue tracker

Issues live as GitHub issues in this repo, worked through the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical triage labels used as-is (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Frontend conventions

The `frontend/` app is built on the `satnaing/shadcn-admin` boilerplate (React 19 + Vite + TanStack Router/Query/Table + Tailwind v4). Every component written must follow:

1. **Path aliases** from `frontend/components.json` - UI primitives as `@/components/ui/...`, other components as `@/components/...`, helpers as `@/lib/utils` (also `@/lib`, `@/hooks`). No relative imports that cross these.
2. **Icons** - use `lucide-react` (the configured `iconLibrary`). Don't add another icon package.
3. **Strict TypeScript** - `strict` on; no `any` escape hatches; type all props and handlers.
4. **No new dependencies without asking** - reuse existing `@/components/ui/*` primitives first; ask before installing anything.

### State management

Four tiers, chosen by what the state is:

- **Server state** (anything fetched from the backend) -> TanStack Query. Never mirror backend data into zustand.
- **Global client state** (cross-feature: auth, user prefs) -> a zustand store in `src/stores/` (e.g. `auth-store`).
- **Feature-scoped UI state** (dialog open, selected row, table filters local to one feature) -> a React Context provider at `features/<x>/components/<x>-provider.tsx` (see `users-provider`, `tasks-provider`).
- **Ephemeral component state** -> `useState`.

### Types (API contract)

Generate TypeScript types from the backend's OpenAPI spec (FastAPI exposes `/api/openapi.json` in dev) with `openapi-typescript` via a `gen:api` script - don't hand-write API types. Hand-write the axios client and TanStack Query hooks yourself, typed against the generated types. Reserve `features/<x>/data/types.ts` for UI-only view models the API doesn't cover.

### Data fetching

- Shared axios instance in `src/lib/api.ts`: `baseURL` from `VITE_API_BASE_URL` (default `/api/v1` for same-origin prod); a request interceptor attaches the auth token via a `getToken()` seam (the auth mechanism, Supabase JWT in prod, plugs in there later).
- Per feature in `features/<x>/data/`: `api.ts` (axios fetchers), `queries.ts` (TanStack Query hooks + a `<feature>Keys` factory: `all`, `lists()`, `detail(id)`), alongside the existing `schema.ts` (zod) and `types.ts`.
- Server state lives only in TanStack Query (see State management). Errors flow through the `QueryClient` in `main.tsx` (retry, 401 session-expiry, 500).

### Routing

File-based TanStack Router. `routes/__root.tsx` is the root; `routeTree.gen.ts` is generated - don't hand-edit it. Guarded app screens go under `routes/_authenticated/<feature>/`; unauthenticated auth pages under `routes/(auth)/`; error pages under `routes/(errors)/`. Use a `route.tsx` for group layout/guard logic.

### Forms

react-hook-form + zod (`@hookform/resolvers/zod`) + the shadcn `form.tsx` primitives. One zod schema per form in `features/<x>/data/schema.ts`; the form component calls `useForm({ resolver: zodResolver(schema) })`.

### Errors & loading

Global errors flow through the `QueryClient` in `main.tsx` (retry policy, 401 -> session reset + sign-in redirect, 500 -> toast + error page in prod). Mutations surface feedback via `sonner` toasts. Loading states use `ui/skeleton.tsx` skeletons, not spinners.
