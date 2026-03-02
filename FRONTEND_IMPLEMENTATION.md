# FRONTEND_IMPLEMENTATION.md

**Version**: 0.1.0  
**Last Updated**: 2026-03-02  
**Frozen**: 2026-03-02  
**Status**: FROZEN - No changes without explicit approval  
**Prerequisite**: Read FRONTEND_CONTRACT.md first

---

## 0. FINAL PLAN — OPENCODE EXECUTION DIRECTIVE

**Status**: Architecture Frozen  
**Source of Truth**: FRONTEND_IMPLEMENTATION.md (this document, verbatim)  
**Deviation Policy**: ❌ No deviations without explicit approval

### 1. Non-Negotiables (Absolute Rules)

Opencode must not:

- Add or modify backend-derived types outside `src/types/api.ts`
- Import `apiFetch` into server components
- Perform authenticated data fetching in RSC
- Store server truth in Zustand
- Optimistically render assistant output
- Add retries, interceptors, or "smart" behavior to `apiFetch`
- Implement UI workarounds for missing backend features
- Auto-ingest documents
- Mutate streamed assistant content
- Add global CSS outside Tailwind/shadcn rules

If any of the above occur, the change is invalid by definition.

### 2. Execution Order (Must Be Followed)

Opencode must implement strictly in this order:

1. **Project foundation**
   - Next.js app bootstrapped
   - Tailwind + shadcn installed
   - Empty build passes

2. **API client layer**
   - `apiFetch` (boring, strict, client-only)
   - Streaming helper with AbortSignal
   - Manual testing against backend

3. **Auth & session**
   - Login/register
   - `/auth/me` wired into session store

4. **Wizard gating**
   - Implemented in root layout
   - Root layout must render nothing (or a blocking shell) until wizard state is resolved
   - No protected route renders before wizard resolution

5. **Chat streaming**
   - Append-only rendering
   - Cancellation works
   - No optimistic UI

6. **Capabilities**
   - Fetched once per session
   - Gating affects visibility and behavior

7. **Docs / RAG**

8. **Admin dashboard**

9. **Settings**

Skipping ahead is not allowed.

### 3. Definition of "Done" for Each Phase

A phase is not complete unless:

- TypeScript build passes
- ESLint passes
- No checklist violations are introduced
- Feature works without reading backend code
- Errors are surfaced, not hidden

Partial completion is not completion.

### 4. Error Semantics (Must Match Exactly)

| Error | Action |
|-------|--------|
| 401 | redirect to /login |
| 501 | render `<FeatureUnavailable />` |

- No silent failures
- No infinite spinners
- No "best effort" fallbacks

Errors are data, not UX polish problems.

### 5. Streaming Rules (Audit-Critical)

- Assistant output is append-only
- No mutation of previous tokens
- No smoothing, rewriting, or animation tricks
- Streaming == data replication, not UX flair

If output differs from backend truth, it is a bug.

### 6. PR Acceptance Gate

Every PR must be evaluated against:

- Section 17: PR Rejection Checklist
- Section 18: "How This Can Still Go Wrong"

If a reviewer hesitates, the answer is reject.

### 7. Mental Model Opencode Must Follow

- Frontend is a strict contract consumer
- Backend is the only source of truth
- UI hides nothing that the backend disallows
- "Boring" is a success metric
- Predictability > cleverness
- Rejection is a design tool

### 8. Final Instruction to Opencode

Implement exactly what is written.  
Do not improve it.  
Do not generalize it.  
Do not anticipate future needs.  
When uncertain, stop and ask.

---

## 1. Stack Decision

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 14+ (App Router) + TypeScript | Native streaming support, SSR, best AI UI ecosystem |
| Build | Next.js built-in | Zero config, dev≈prod, streaming cohesion |
| Styling | Tailwind CSS + shadcn/ui | Atomic CSS, component portability, no runtime cost |
| State | Zustand | Lightweight, pairs with shadcn, but kept thin |
| HTTP | fetch + ReadableStream | Better cancellation, auth handling than EventSource |

**Constraints**:
- 130 character line width (match backend)
- No custom CSS frameworks
- Minimal global styles, token-driven theming
- Styles live next to components

**RSC Policy**:
- All data-fetching that depends on authenticated user state MUST occur in client components.
- Server components may render layout/shell only.
- `apiFetch` is client-only by design and must not be imported into server components.

---

## 2. Project Foundation

### 2.1 Initialize Next.js Project

```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --src-dir \
  --import-alias "@/*" \
  --no-git
```

### 2.2 Install shadcn/ui

```bash
cd frontend
npx shadcn-ui@latest init

# Core components needed
npx shadcn-ui@latest add button input textarea card dialog 
npx shadcn-ui@latest add dropdown-menu select tabs avatar 
npx shadcn-ui@latest add badge separator toast scroll-area
npx shadcn-ui@latest add table form label
```

### 2.3 Directory Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/              # Login, register (unauthenticated)
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   ├── (main)/              # Protected routes
│   │   │   ├── chat/
│   │   │   │   └── page.tsx
│   │   │   ├── docs/
│   │   │   │   ├── page.tsx     # List + create
│   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx # View/edit
│   │   │   │   └── search/
│   │   │   │       └── page.tsx
│   │   │   ├── admin/
│   │   │   │   ├── page.tsx     # Dashboard
│   │   │   │   ├── users/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── audit/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── config/
│   │   │   │       └── page.tsx
│   │   │   └── settings/
│   │   │       ├── page.tsx     # Profile
│   │   │       └── sessions/
│   │   │           └── page.tsx
│   │   ├── wizard/              # First-run mode (blocks everything else)
│   │   │   └── page.tsx
│   │   ├── layout.tsx          # Root layout with providers
│   │   └── page.tsx             # → /chat (default)
│   ├── components/
│   │   ├── ui/                  # shadcn components (copy-in)
│   │   ├── chat/                # Chat-specific
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatSidebar.tsx
│   │   │   └── ImageUploader.tsx
│   │   ├── docs/                # Document-specific
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentEditor.tsx
│   │   │   └── SearchResults.tsx
│   │   ├── admin/               # Admin-specific
│   │   │   ├── UserTable.tsx
│   │   │   ├── AuditLog.tsx
│   │   │   └── ConfigForm.tsx
│   │   ├── auth/                # Auth components
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   └── wizard/              # Wizard components
│   │       ├── AdminCreate.tsx
│   │       └── DataMigration.tsx
│   ├── hooks/
│   │   ├── useSession.ts
│   │   ├── useCapabilities.ts
│   │   ├── useWizard.ts
│   │   └── useStreamingChat.ts
│   ├── guards/
│   │   ├── requireAuth.ts
│   │   ├── requireAdmin.ts
│   │   └── requireWizardComplete.ts
│   ├── lib/
│   │   ├── api.ts               # Centralized API client
│   │   ├── capabilities.ts      # Capability helpers
│   │   └── utils.ts
│   └── types/
│       └── api.ts               # Contract-derived types
├── tailwind.config.ts
├── next.config.js
└── package.json
```

---

## 3. API Client Layer (Critical)

### 3.1 Core Responsibilities

File: `src/lib/api.ts`

This is the single most important frontend file. It must be **boring and strict**.

| Responsibility | Implementation |
|----------------|-----------------|
| Error normalization | Transform all errors to canonical envelope |
| Error body handling | Error responses may be empty, HTML, or malformed JSON - must tolerate this |
| Error assumptions | Components must not assume structured error payloads unless ApiError is explicitly returned |
| 401 handling | Redirect to `/login` |
| 501 handling | Return feature unavailable signal |
| No auto-retry | Fail loudly on non-200s |
| No clever interceptors | Explicit is better than implicit |

### 3.2 Type-Safe Fetch Wrapper

```typescript
// Helper for safe JSON parsing
async function safeJson(res: Response) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

// src/lib/api.ts (pseudo-code - actual implementation needed)

type ApiError = {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    credentials: 'include', // Include HTTP-only cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  // Handle 401 - redirect to login
  // NOTE: apiFetch is client-only. Guard for server components.
  if (typeof window !== 'undefined' && response.status === 401) {
    window.location.href = '/login';
    throw new Error('UNAUTHORIZED');
  }

  // Handle 501 - feature not available
  if (response.status === 501) {
    const data = await safeJson(response);
    throw new Error(`NOT_IMPLEMENTED: ${data?.error?.message || 'Feature not available'}`);
  }

  // Fail on other errors
  if (!response.ok) {
    const data = await safeJson(response);
    throw new Error(data?.error?.message || `HTTP ${response.status}`);
  }

  return response.json();
}
```

#### Optional: ApiResult<T> Wrapper

For cleaner error handling without try/catch soup, consider using an explicit result type:

```typescript
// src/lib/api.ts

type ApiError = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };

// Alternative: apiFetchResult that returns ApiResult instead of throwing
async function apiFetchResult<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResult<T>> {
  try {
    const data = await apiFetch<T>(endpoint, options);
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return {
      ok: false,
      error: { code: 'UNKNOWN', message, details: { originalError: String(err) } }
    };
  }
}

// Usage in components:
// const result = await apiFetchResult<User>('/auth/me');
// if (!result.ok) { return <ErrorDisplay error={result.error} /> }
// return <UserProfile user={result.data} />;
```

### 3.3 SSE Streaming Helper

```typescript
// WARNING: Do not refactor for UX smoothing.
// This parser preserves backend truth, not visual polish.
// Streaming == data replication, not animation.

// Use fetch + ReadableStream, NOT EventSource
async function* streamChat(
  message: string,
  sessionId?: string,
  images?: string[],
  signal?: AbortSignal
) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    credentials: 'include',
    signal, // Pass AbortSignal for proper cancellation
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, images }),
  });

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        yield data;
      }
    }
  }
}
```

**Streaming notes**:
- Chunks may split JSON or lines arbitrarily
- Implementation must buffer incomplete lines across reads
- Current implementation assumes newline-aligned chunks for simplicity (sufficient for MVP)
- TODO: Upgrade to buffered line parser for production robustness

---

## 4. Types (Contract-Derived)

### 4.1 Core Types

File: `src/types/api.ts`

Must mirror FRONTEND_CONTRACT.md exactly.

**Important**: Types in src/types/api.ts are read-only mirrors of the backend contract.
They must not include frontend-only fields or helpers.

```typescript
// User
interface User {
  id: string;          // UUIDv4
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string; // ISO-8601 UTC
}

// Session
interface Session {
  session_id: string;
  user_id: string;
  issued_at: string;
  expires_at: string;
  last_activity: string;
  revoked: boolean;
}

// Chat
interface ChatMessage {
  msg_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// Document
interface Document {
  id: string;
  title: string;
  visibility: 'private' | 'public';
  categories: string[];
  source: string | null;
  created_at: string;
  updated_at: string | null;
}

// Search Result
interface SearchResult {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  modality: 'text' | 'image';
}

// Capabilities
interface Capabilities {
  capabilities: {
    filesystem: { enabled: boolean; allowed_paths: string[] };
    web: { enabled: boolean; interact_enabled: boolean };
    comfyui: { enabled: boolean };
    tts: { enabled: boolean };
    multimodal: { enabled: boolean };
    tools: {
      exec_python: 'blocked';
      exec_shell: 'blocked';
      web_search: 'available' | 'disabled';
      web_fetch: 'available' | 'disabled';
      web_crawl: 'available' | 'disabled';
    };
  };
}

// Tool
interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

// Audit Event
interface AuditEvent {
  id: string;
  timestamp: string;
  user_id: string | null;
  event_type: string;
  details: Record<string, unknown>;
  request_id: string | null;
}

// Canonical Error
interface ApiError {
  error: {
    code: 'UNAUTHORIZED' | 'INVALID_CREDENTIALS' | 'SESSION_EXPIRED' |
          'FORBIDDEN' | 'ACCESS_DENIED' | 'NOT_FOUND' | 'NOT_IMPLEMENTED' |
          'VALIDATION_ERROR' | 'BAD_REQUEST';
    message: string;
    details?: Record<string, unknown>;
  };
}
```

---

## 5. State Management (Zustand - Thin)

### 5.1 Allowed Store Usage

| Store | Contents | Notes |
|-------|----------|-------|
| session | user, isAuthenticated, sessionId | Derived from /auth/me |
| capabilities | Cached from /config/capabilities | Fetched once per session |
| ui | sidebarOpen, theme, etc | Local preferences only |

### 5.2 NOT Allowed in Stores

- Chat message history (derive from route/session)
- Server truth / config mirrors
- Document content (fetch on demand)

### 5.3 Store Example

```typescript
// src/lib/store.ts

// This store is UI/session glue ONLY.
// Adding server truth here is a PR rejection reason.

import { create } from 'zustand';

interface SessionState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  isAuthenticated: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
}));
```

---

## 6. Custom Hooks

### 6.1 useSession

```typescript
// src/hooks/useSession.ts
import { useEffect } from 'react';
import { useSessionStore } from '@/lib/store';
import { apiFetch } from '@/lib/api';

export function useSession() {
  const { user, setUser, isAuthenticated } = useSessionStore();

  useEffect(() => {
    if (!isAuthenticated) {
      apiFetch<User>('/auth/me')
        .then(setUser)
        .catch(() => setUser(null));
    }
  }, []);

  return { user, isAuthenticated };
}
```

**Note**: If `setUser(null)` runs once, the effect won't retry on subsequent renders. Consider tracking a `hasFetchedSession` flag, or document that a page reload is required after logout.

### 6.2 useCapabilities

```typescript
// src/hooks/useCapabilities.ts
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import type { Capabilities } from '@/types/api';

export function useCapabilities() {
  const [capabilities, setCapabilities] = useState<Capabilities['capabilities'] | null>(null);

  useEffect(() => {
    apiFetch<Capabilities>('/config/capabilities')
      .then((res) => setCapabilities(res.capabilities))
      .catch(() => setCapabilities(null));
  }, []);

  return capabilities;
}
```

### 6.3 useStreamingChat

```typescript
// src/hooks/useStreamingChat.ts
import { useState, useCallback, useRef } from 'react';
import { streamChat } from '@/lib/api';

interface UseStreamingChatOptions {
  sessionId?: string;
  onComplete?: () => void;
}

export function useStreamingChat({ sessionId, onComplete }: UseStreamingChatOptions = {}) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(async (message: string, images?: string[]) => {
    setIsStreaming(true);
    setContent('');
    abortRef.current = new AbortController();

    try {
      for await (const event of streamChat(message, sessionId, images, abortRef.current.signal)) {
        if (event.type === 'assistant_delta') {
          setContent((prev) => prev + event.data.content);
        } else if (event.type === 'done') {
          break;
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        return; // Gracefully handle cancellation
      }
      throw err;
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
      onComplete?.();
    }
  }, [sessionId, onComplete]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { content, isStreaming, send, cancel };
}
```

**Important**: Streaming events are append-only; no mutation of previous assistant output is allowed. This ensures auditability and debuggability.

---

## 7. Execution Order

| Phase | Tasks | Rationale |
|-------|-------|-----------|
| 1 | Project foundation | Next.js + shadcn + types |
| 2 | API client layer | Critical path - fail fast if wrong |
| 3 | Auth + session | Everything depends on this |
| 4 | Wizard flow | Blocks access until complete |
| 5 | Chat streaming | Core value proposition |
| 6 | Capabilities gating | Gates all feature visibility |
| 7 | Docs/RAG | Authoring + retrieval |
| 8 | Admin dashboard | Users, audit, config |
| 9 | Settings | Profile, sessions |

---

## 8. Phase-by-Phase Implementation

### Phase 1: Project Foundation

1. Run `npx create-next-app@latest frontend`
2. Configure `tailwind.config.ts` with 130 char line width
3. Run shadcn init and install components
4. Create `src/types/api.ts` with all contract types
5. Verify empty shell builds: `npm run build`

### Phase 2: API Client Layer

1. Create `src/lib/api.ts` with fetch wrapper
2. Implement SSE streaming helper
3. Add error normalization (401 → redirect, 501 → signal)
4. Test against live backend endpoints

### Phase 3: Authentication

1. Create `(auth)/login/page.tsx`
2. Create `(auth)/register/page.tsx`
3. Implement LoginForm component with error display
4. Handle cookie-based session (automatic with credentials: include)
5. Test login flow end-to-end

### Phase 4: Wizard Flow

**IMPORTANT**: Wizard gating must happen in root layout (`src/app/layout.tsx`), NOT in `wizard/page.tsx`. This prevents protected routes from briefly rendering before redirect.

1. Create `wizard/page.tsx`
2. In root layout, fetch wizard status on app init
3. If state is `not_started` or `needs_setup_with_existing_data`:
   - Show wizard as full-screen mode (layout blocks all other routes)
4. Implement admin creation flow
5. On completion: redirect to `/chat`
6. Once completed, wizard routes should permanently redirect away

### Phase 5: Chat Interface

1. Create `(main)/chat/page.tsx`
2. Implement ChatMessage component (user + assistant)
3. Implement ChatInput with Shift+Enter for newline
4. Integrate useStreamingChat hook
5. Render markdown (use `react-markdown` or similar)
6. Add image upload for multimodal (if capabilities allow)
7. **NO optimistic UI** - render only what arrives

### Phase 6: Capabilities Gating

1. Fetch capabilities once on session init
2. Store in Zustand (not re-fetched per page)
3. Create capability check helpers:
   ```typescript
   const canUseFilesystem = capabilities?.filesystem?.enabled;
   const canUseWebSearch = capabilities?.tools?.web_search === 'available';
   const canUseMultimodal = capabilities?.multimodal?.enabled;
   ```
4. Conditionally render features based on capabilities

**Important**: Capabilities must affect visibility AND behavior. Hidden features must still fail safely if accessed directly (defense in depth).

### Phase 7: Documents & RAG

1. Create `(main)/docs/page.tsx` - document list
2. Create document CRUD operations
3. Create `(main)/docs/[id]/page.tsx` - view/edit
4. Create `(main)/docs/search/page.tsx` - search UI
5. Display search results with chunk highlighting
6. **Never auto-ingest** - explicit ingestion only

### Phase 8: Admin Dashboard

1. Create `(main)/admin/page.tsx` - admin landing
2. Protect with role check (admin only)
3. Create user management (`admin/users/page.tsx`)
4. Create audit log viewer (`admin/audit/page.tsx`)
   - Read-only forever (no delete/clear)
5. Create system config (`admin/config/page.tsx`)
   - Model configuration forms
   - Test model connection UI

### Phase 9: Settings

1. Create `(main)/settings/page.tsx` - profile
2. Create `(main)/settings/sessions/page.tsx`
3. List active sessions with revoke option

---

## 9. Component Guidelines

### 9.0 Shared Components

#### FeatureUnavailable

For consistent handling of 501 (NOT_IMPLEMENTED) responses across the app:

```typescript
// src/components/FeatureUnavailable.tsx
interface FeatureUnavailableProps {
  feature?: string;
  message?: string;
}

export function FeatureUnavailable({
  feature = 'This feature',
  message = 'is disabled or not available in this deployment.'
}: FeatureUnavailableProps) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="text-center">
        <div className="text-muted-foreground mb-2">
          <span className="text-2xl">🚫</span>
        </div>
        <h3 className="font-medium text-lg">{feature}</h3>
        <p className="text-muted-foreground text-sm">{message}</p>
      </div>
    </div>
  );
}
```

**Usage in components:**
```typescript
// When capability is not available
if (capabilities?.tools?.web_search !== 'available') {
  return <FeatureUnavailable feature="Web Search" />;
}

// When 501 is caught
} catch (err) {
  if (err instanceof Error && err.message.includes('NOT_IMPLEMENTED')) {
    return <FeatureUnavailable />;
  }
  throw err;
}
```

### 9.1 Chat Components

| Component | Responsibility |
|-----------|----------------|
| ChatMessage | Single message display (role, content, timestamp) |
| ChatInput | Text input with Enter to send, Shift+Enter for newline |
| ChatSidebar | Session history, new chat button |
| ImageUploader | Base64 encoding with `data:image/*` prefix |

### 9.2 Document Components

| Component | Responsibility |
|-----------|----------------|
| DocumentList | Paginated list with filters |
| DocumentEditor | Title, content, visibility, categories |
| SearchResults | Results with score, chunk preview |

### 9.3 Admin Components

| Component | Responsibility |
|-----------|----------------|
| UserTable | User list with edit/activate/deactivate |
| AuditLog | Filterable event table (read-only) |
| ConfigForm | Model config with test connection |

---

## 10. Error Handling

### 10.1 Frontend Error Contract

| Error Code | HTTP Status | Frontend Action |
|------------|-------------|-----------------|
| UNAUTHORIZED | 401 | Redirect to /login |
| INVALID_CREDENTIALS | 401 | Show "Invalid username or password" |
| SESSION_EXPIRED | 401 | Redirect to /login |
| FORBIDDEN | 403 | Show "Admin access required" |
| ACCESS_DENIED | 403 | Show "You don't have access to this resource" |
| NOT_FOUND | 404 | Show "Resource not found" |
| NOT_IMPLEMENTED | 501 | Show `<FeatureUnavailable />` |
| VALIDATION_ERROR | 422 | Show field-level errors |
| BAD_REQUEST | 400 | Show generic error message |

### 10.2 Error Display

- Use shadcn `Toast` component for transient errors
- Show inline errors for form fields
- Never silently swallow errors
- For 501 (NOT_IMPLEMENTED): use the `<FeatureUnavailable />` component for consistent UI

---

## 11. Security Requirements

| Rule | Implementation |
|------|----------------|
| HTTP-only cookies | Use `credentials: 'include'` on all fetches |
| No token storage | Never store tokens in localStorage |
| Role-based access | Check user.role before rendering admin routes |
| Input sanitization | Use React's default escaping |
| No credential logging | Never log cookies or auth headers |

---

## 12. Alpha Guardrails (Contributors Must Follow)

```
❌ NO backend logic duplication
❌ **NO frontend-side caching of config truth**
❌ NO UI "workarounds" for contract gaps
❌ NO optimistic UI for assistant messages
❌ NO auto-ingest on document save
❌ NO deletion of audit logs (even if backend allows)

✅ BACKEND CONTRACT IS LAW
✅ 501 means "intentionally unavailable in this deployment."
✅ Capabilities cached once per session
✅ Explicit ingestion only
```

---

## 13. Testing Strategy

### 13.1 Unit Tests

- API client error handling
- Capability helpers
- Utility functions

### 13.2 Integration Tests

- Auth flow (login, logout, session refresh)
- Chat streaming (connect, stream, disconnect)
- Document CRUD
- Admin user management

### 13.3 E2E (Future)

- Full user journey: login → chat → logout
- Admin flow: login → admin → config → logout

---

## 14. Linting & Type Checking

```bash
# TypeScript strict mode
npm run build          # Includes type check

# ESLint
npm run lint

# Pre-commit hook (recommended)
npx husky add .husky/pre-commit "npm run lint"
```

---

## 15. Non-Goals (Out of Scope)

The following are intentionally NOT implemented in v1 frontend:

- exec_python tool (always 501)
- exec_shell tool (always 501)
- Attachment ingestion/processing (always 501)
- TTS playback UI
- STT (Speech-to-Text)
- Real-time collaboration
- Webhooks
- API rate limiting UI
- MFA

---

## 16. Success Criteria

The frontend implementation is complete when:

- [ ] All authenticated endpoints respond correctly
- [ ] SSE streaming works with proper cancellation
- [ ] Capabilities gating hides unavailable features
- [ ] Admin dashboard is fully functional
- [ ] No frontend-side business logic
- [ ] All 501s display appropriate "not available" UI
- [ ] Audit logs are read-only
- [ ] Build passes with no TypeScript errors
- [ ] ESLint passes with no warnings
- [ ] A frontend developer can build features without reading backend code

---

## 17. PR Rejection Checklist

Use this as a hard gate. If any item below is violated, the PR must be rejected or sent back.

### A. Contract & API Violations (Automatic Reject)

Reject if:
- [ ] Frontend types were added/modified in `src/types/api.ts` without a corresponding backend contract change
- [ ] Frontend-only fields, helpers, or flags were added to contract-derived types
- [ ] Backend logic is duplicated client-side (e.g. permission logic, config derivation)
- [ ] `apiFetch` semantics were changed (retry logic, interceptors, silent handling)
- [ ] Errors are swallowed, logged only, or converted into "fallback success"
- [ ] 501 (NOT_IMPLEMENTED) is treated as an error instead of "intentionally unavailable"

**Rationale**: Backend contract is law. Violations create silent drift.

### B. RSC / Data Fetching Violations (High Severity)

Reject if:
- [ ] Authenticated data fetching occurs in a Server Component
- [ ] `apiFetch` is imported into a Server Component
- [ ] Cookies/session-dependent logic runs in RSC
- [ ] Server components attempt to "optimize" by preloading user data

**Rationale**: This will break unpredictably across environments.

### C. State Management Abuse (High Severity)

Reject if:
- [ ] Chat message history is stored in Zustand
- [ ] Document content is stored globally instead of fetched per route
- [ ] Server truth (config, capabilities, permissions) is cached beyond session rules
- [ ] Zustand stores grow beyond UI/session glue
- [ ] Store mutations perform network requests

**Rationale**: This guarantees stale state bugs.

### D. Streaming & Chat Violations (High Severity)

Reject if:
- [ ] Assistant messages are optimistically rendered
- [ ] Previously streamed assistant output is mutated or rewritten
- [ ] Streaming is implemented with EventSource instead of fetch + ReadableStream
- [ ] Abort/cancellation is ignored or removed
- [ ] Errors during streaming are silently swallowed

**Rationale**: Violates auditability and correctness.

### E. Capabilities & Feature Gating Violations

Reject if:
- [ ] Feature visibility is gated but backend access is not handled safely
- [ ] Capabilities are fetched repeatedly per page without reason
- [ ] Feature flags are inferred client-side instead of read from capabilities
- [ ] A hidden feature "mostly works" if accessed directly

**Rationale**: Security-through-UI is not security.

### F. Wizard & Access Control Violations

Reject if:
- [ ] Wizard gating happens in page components instead of root layout
- [ ] Protected routes briefly render before redirect
- [ ] Wizard state is cached or inferred client-side
- [ ] Admin routes render without role verification

**Rationale**: Leads to privilege leaks and UX glitches.

### G. UI / UX Anti-Patterns

Reject if:
- [ ] UI workarounds compensate for missing backend behavior
- [ ] "Temporary" hacks are added without contract changes
- [ ] Global CSS or styling systems bypass Tailwind/shadcn rules
- [ ] Errors are hidden behind loading spinners indefinitely

**Rationale**: Tech debt injection.

### H. Cultural Red Flags (Reviewer Judgment)

Strongly consider rejection if you see:
- [ ] "Just this once" language in the PR description
- [ ] Defensive explanations instead of contract references
- [ ] Large diffs touching many layers without a clear reason
- [ ] "We can clean this up later" comments

---

## 18. How This Can Still Go Wrong

This section assumes good intentions but highlights where teams usually fail anyway.

### 1. Slow Drift Away From the Contract

**How it happens**: Someone adds a tiny frontend-only helper field to a contract type. "It's harmless." Six weeks later the frontend depends on it.

**Result**: Backend and frontend silently diverge. Changes become scary. Integration bugs become mysterious.

**Defense**: PR checklist item: types are mirrors only. Reject early, even for "tiny" changes.

### 2. "Smart" API Abstractions Sneaking In

**How it happens**: Someone dislikes try/catch. Adds retries, interceptors, or auto-refresh logic. Hides failure semantics.

**Result**: Backend failures become non-deterministic. Debugging requires reading invisible logic. 501 semantics get lost.

**Defense**: Keep `apiFetch` boring. Explicit failures > clever recoveries.

### 3. Zustand Becoming a Shadow Backend

**How it happens**: "Let's cache this to avoid refetching." "We already have this in the store." "It's just config."

**Result**: Two sources of truth. Stale permissions. Impossible-to-reproduce bugs.

**Defense**: Session-only caching. Server truth always fetched explicitly.

### 4. Streaming Optimizations That Break Auditability

**How it happens**: Someone wants smoother UX. Rewrites previous assistant output. Adds optimistic tokens.

**Result**: Assistant output no longer reflects backend truth. Audit logs lose meaning. Debugging becomes impossible.

**Defense**: Append-only rule is sacred. Streaming is data, not animation.

### 5. Wizard Logic Eroding Over Time

**How it happens**: Wizard completion logic spreads into pages. Someone adds a bypass "for convenience." Gating becomes conditional and fragmented.

**Result**: Users slip into half-initialized states. Admin-only paths leak.

**Defense**: Single choke point: root layout. Wizard logic lives nowhere else.

### 6. Capability Gating Becoming Cosmetic

**How it happens**: Feature is hidden in UI. Backend still errors. Error handling isn't wired up.

**Result**: Direct navigation breaks. Security assumptions fail. Users see raw errors.

**Defense**: Visibility AND behavior must be gated. 501 always maps to FeatureUnavailable.

### 7. "MVP" Hacks Becoming Permanent

**How it happens**: MVP shortcuts are undocumented. TODOs aren't explicit. New devs assume behavior is correct.

**Result**: Temporary compromises fossilize. Future fixes look like regressions.

**Defense**: Explicit limitations (like you already did). Document why something is "good enough for now."

### 8. Review Fatigue

**How it happens**: Docs are solid. Reviewers stop enforcing them. Exceptions accumulate quietly.

**Result**: Architecture decays without a single big mistake.

**Defense**: Use the checklist ruthlessly. Reject early, reject often, reject calmly.

---

## 19. References

- FRONTEND_CONTRACT.md - Backend API contract
- AGENTS.md - Backend development guide
- shadcn/ui documentation
- Next.js App Router documentation

---

**End of Implementation Guide**
