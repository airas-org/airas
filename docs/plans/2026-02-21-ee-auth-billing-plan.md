# EE Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add enterprise authentication (Supabase Auth) to AIRAS under `ee/` directories with ELv2 license, keeping OSS behavior unchanged. Authentication only (no billing for now).

**Architecture:** Frontend uses Supabase JS SDK for OAuth login (Google/GitHub), backend verifies JWT with PyJWT. `ENTERPRISE_ENABLED` env var toggles the entire EE stack on/off.

**Tech Stack:** Supabase Auth, PyJWT, FastAPI, React, Axios

---

## Task 1: EE directory scaffolding and licenses

**Files:**
- Create: `frontend/src/ee/LICENSE`
- Create: `backend/api/ee/__init__.py`
- Create: `backend/api/ee/LICENSE`
- Create: `backend/api/ee/auth/__init__.py`
- Create: `frontend/src/ee/config.ts`
- Create: `frontend/src/ee/auth/lib/.gitkeep`
- Create: `frontend/src/ee/auth/hooks/.gitkeep`
- Create: `frontend/src/ee/auth/components/.gitkeep`

**Step 1: Create directories and ELv2 LICENSE files**

Create the ELv2 license text in both `frontend/src/ee/LICENSE` and `backend/api/ee/LICENSE`. Use the official Elastic License 2.0 text with `Licensor: AIRAS`.

**Step 2: Create frontend EE config**

```typescript
// frontend/src/ee/config.ts
export const isEnterpriseEnabled = (): boolean =>
  import.meta.env.VITE_ENTERPRISE_ENABLED === "true";
```

**Step 3: Create backend `__init__.py` files**

Empty `__init__.py` files in `backend/api/ee/`, `backend/api/ee/auth/`, `backend/api/ee/billing/`.

**Step 4: Commit**

```bash
git add frontend/src/ee/ backend/api/ee/
git commit -m "feat(ee): scaffold EE directory structure with ELv2 licenses"
```

---

## Task 2: Backend — Add PyJWT dependency

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add dependencies to pyproject.toml**

Add to the `[project.dependencies]` section:

```toml
"PyJWT[crypto]>=2.8.0",
```

**Step 2: Install dependencies**

```bash
cd backend && uv sync
```

**Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "feat(ee): add PyJWT dependency"
```

---

## Task 3: Backend — EE settings and configuration

**Files:**
- Create: `backend/api/ee/settings.py`
- Modify: `.env.example`

**Step 1: Create EE settings module**

```python
# backend/api/ee/settings.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EESettings:
    enabled: bool
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str


def get_ee_settings() -> EESettings:
    return EESettings(
        enabled=os.getenv("ENTERPRISE_ENABLED", "false").lower() == "true",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
    )
```

**Step 2: Update `.env.example`**

Append the EE section:

```
# Enterprise Edition (optional)
ENTERPRISE_ENABLED=false
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
VITE_ENTERPRISE_ENABLED=false
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

**Step 3: Commit**

```bash
git add backend/api/ee/settings.py .env.example
git commit -m "feat(ee): add EE settings and env vars"
```

---

## Task 4: Backend — JWT authentication middleware

**Files:**
- Create: `backend/api/ee/auth/middleware.py`
- Create: `backend/api/ee/auth/dependencies.py`
- Modify: `backend/api/schemas/assisted_research.py` (update `get_current_user_id`)
- Modify: `backend/api/main.py` (conditionally register EE)

**Step 1: Create JWT verification middleware**

```python
# backend/api/ee/auth/middleware.py
from uuid import UUID

import jwt
from fastapi import HTTPException, Request, status

from api.ee.settings import get_ee_settings


def verify_jwt(token: str) -> dict:
    """Verify Supabase JWT and return payload."""
    settings = get_ee_settings()
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def extract_user_id_from_request(request: Request) -> UUID:
    """Extract and verify user ID from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header.removeprefix("Bearer ")
    payload = verify_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub claim",
        )
    return UUID(sub)
```

**Step 2: Create auth dependencies**

```python
# backend/api/ee/auth/dependencies.py
from uuid import UUID

from fastapi import Depends, Request

from api.ee.auth.middleware import extract_user_id_from_request
from api.ee.settings import get_ee_settings

SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_current_user_id(request: Request) -> UUID:
    """Return user ID from JWT if EE is enabled, otherwise return SYSTEM_USER_ID."""
    settings = get_ee_settings()
    if not settings.enabled:
        return SYSTEM_USER_ID
    return extract_user_id_from_request(request)
```

**Step 3: Update existing `get_current_user_id` references**

Modify `backend/api/schemas/assisted_research.py`:
- Remove the local `get_current_user_id()` function and `SYSTEM_USER_ID`
- Import from `api.ee.auth.dependencies` instead

Search all files that import `get_current_user_id` from `api.schemas.assisted_research` and update the import path to `api.ee.auth.dependencies`.

**Step 4: Conditionally register EE routes in main.py**

Add to `backend/api/main.py` after the existing router registrations:

```python
from api.ee.settings import get_ee_settings

# Register EE routes if enterprise is enabled
ee_settings = get_ee_settings()
if ee_settings.enabled:
    from api.ee.auth.routes import router as ee_auth_router

    app.include_router(ee_auth_router, prefix="/airas/ee")
```

**Step 5: Commit**

```bash
git add backend/api/ee/auth/ backend/api/schemas/assisted_research.py backend/api/main.py
git commit -m "feat(ee): add JWT authentication middleware and dependencies"
```

---

## Task 5: Backend — Auth routes

**Files:**
- Create: `backend/api/ee/auth/routes.py`

**Step 1: Create auth routes**

```python
# backend/api/ee/auth/routes.py
from uuid import UUID

from fastapi import APIRouter, Depends

from api.ee.auth.dependencies import get_current_user_id

router = APIRouter(prefix="/auth", tags=["ee-auth"])


@router.get("/me")
async def get_me(user_id: UUID = Depends(get_current_user_id)):
    """Return the current authenticated user's ID."""
    return {"user_id": str(user_id)}
```

**Step 2: Commit**

```bash
git add backend/api/ee/auth/routes.py
git commit -m "feat(ee): add /ee/auth/me endpoint"
```

---

## Task 6: Frontend — Add Supabase dependency and EE config

**Files:**
- Modify: `frontend/package.json`
- Already created: `frontend/src/ee/config.ts` (Task 1)

**Step 1: Install @supabase/supabase-js**

```bash
cd frontend && npm install @supabase/supabase-js
```

**Step 2: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat(ee): add @supabase/supabase-js dependency"
```

---

## Task 7: Frontend — Supabase client and auth hooks

**Files:**
- Create: `frontend/src/ee/auth/lib/supabase.ts`
- Create: `frontend/src/ee/auth/hooks/useAuth.ts`
- Create: `frontend/src/ee/auth/hooks/useSession.ts`

**Step 1: Create Supabase client**

```typescript
// frontend/src/ee/auth/lib/supabase.ts
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

**Step 2: Create useSession hook**

```typescript
// frontend/src/ee/auth/hooks/useSession.ts
import type { Session } from "@supabase/supabase-js";
import { useEffect, useState } from "react";
import { supabase } from "@/ee/auth/lib/supabase";

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  return { session, loading };
}
```

**Step 3: Create useAuth hook**

```typescript
// frontend/src/ee/auth/hooks/useAuth.ts
import { supabase } from "@/ee/auth/lib/supabase";

export function useAuth() {
  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  };

  const signInWithGithub = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "github",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  };

  return { signInWithGoogle, signInWithGithub, signOut };
}
```

**Step 4: Commit**

```bash
git add frontend/src/ee/auth/
git commit -m "feat(ee): add Supabase client and auth hooks"
```

---

## Task 8: Frontend — Auth components (LoginPage, AuthGuard, AuthCallback, UserMenu)

**Files:**
- Create: `frontend/src/ee/auth/components/LoginPage.tsx`
- Create: `frontend/src/ee/auth/components/AuthGuard.tsx`
- Create: `frontend/src/ee/auth/components/AuthCallback.tsx`
- Create: `frontend/src/ee/auth/components/UserMenu.tsx`

**Step 1: Create LoginPage**

```tsx
// frontend/src/ee/auth/components/LoginPage.tsx
import { useAuth } from "@/ee/auth/hooks/useAuth";

export function LoginPage() {
  const { signInWithGoogle, signInWithGithub } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-8">
        <div className="text-center">
          <img src="/airas_logo.png" alt="AIRAS" className="mx-auto h-12 w-auto" />
          <h1 className="mt-4 text-xl font-semibold text-foreground">
            Sign in to AIRAS
          </h1>
        </div>
        <div className="space-y-3">
          <button
            type="button"
            onClick={signInWithGoogle}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted/60 transition-colors"
          >
            Sign in with Google
          </button>
          <button
            type="button"
            onClick={signInWithGithub}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted/60 transition-colors"
          >
            Sign in with GitHub
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Create AuthGuard**

```tsx
// frontend/src/ee/auth/components/AuthGuard.tsx
import type { ReactNode } from "react";
import { useSession } from "@/ee/auth/hooks/useSession";
import { LoginPage } from "@/ee/auth/components/LoginPage";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { session, loading } = useSession();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
```

**Step 3: Create AuthCallback**

```tsx
// frontend/src/ee/auth/components/AuthCallback.tsx
import { useEffect } from "react";
import { supabase } from "@/ee/auth/lib/supabase";

export function AuthCallback() {
  useEffect(() => {
    supabase.auth.getSession().then(() => {
      // Session is automatically handled by Supabase
      // Redirect to home after callback
      window.location.href = "/";
    });
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-muted-foreground">Signing in...</div>
    </div>
  );
}
```

**Step 4: Create UserMenu**

```tsx
// frontend/src/ee/auth/components/UserMenu.tsx
import { LogOut, UserCircle } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/ee/auth/hooks/useAuth";
import { useSession } from "@/ee/auth/hooks/useSession";

export function UserMenu() {
  const { session } = useSession();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!session) return null;

  const email = session.user.email ?? "";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-muted/60 transition-colors"
      >
        <UserCircle className="h-5 w-5" />
        <span className="max-w-[120px] truncate">{email}</span>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 rounded-md border border-border bg-card shadow-lg z-50">
          <button
            type="button"
            onClick={() => {
              signOut();
              setOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted/60 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
```

**Step 5: Commit**

```bash
git add frontend/src/ee/auth/components/
git commit -m "feat(ee): add LoginPage, AuthGuard, AuthCallback, UserMenu components"
```

---

## Task 9: Frontend — Axios interceptor for JWT

**Files:**
- Create: `frontend/src/ee/auth/lib/axios-interceptor.ts`

**Step 1: Create Axios interceptor**

```typescript
// frontend/src/ee/auth/lib/axios-interceptor.ts
import type { InternalAxiosRequestConfig } from "axios";
import { supabase } from "@/ee/auth/lib/supabase";

export async function authRequestInterceptor(
  config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
}
```

**Step 2: Commit**

```bash
git add frontend/src/ee/auth/lib/axios-interceptor.ts
git commit -m "feat(ee): add Axios auth interceptor"
```

---

## Task 10: Frontend — Integrate EE into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add EE integration to App.tsx**

Import EE components and wrap the app conditionally:

```tsx
// Add imports at top of App.tsx
import { isEnterpriseEnabled } from "@/ee/config";

// Conditionally import EE components
const AuthGuard = isEnterpriseEnabled()
  ? (await import("@/ee/auth/components/AuthGuard")).AuthGuard
  : null;
const UserMenu = isEnterpriseEnabled()
  ? (await import("@/ee/auth/components/UserMenu")).UserMenu
  : null;
const AuthCallback = isEnterpriseEnabled()
  ? (await import("@/ee/auth/components/AuthCallback")).AuthCallback
  : null;
```

Note: Since the project doesn't use React Router, handle `/auth/callback` path check:

```tsx
// At the top of the App component function:
if (isEnterpriseEnabled() && window.location.pathname === "/auth/callback") {
  return <AuthCallbackPage />;
}
```

Replace the existing Login button in the header (lines 244-250) with:

```tsx
{isEnterpriseEnabled() && UserMenu ? (
  <UserMenu />
) : (
  <button
    type="button"
    className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-muted/60 transition-colors"
  >
    <UserCircle className="h-5 w-5" />
    <span>Login</span>
  </button>
)}
```

Wrap the main content with AuthGuard when EE is enabled. Use a lazy-loading approach that avoids top-level await:

```tsx
// Create a wrapper component in App.tsx
function AppWithEE() {
  const [EEComponents, setEEComponents] = useState<{
    AuthGuard: typeof import("@/ee/auth/components/AuthGuard").AuthGuard;
    UserMenu: typeof import("@/ee/auth/components/UserMenu").UserMenu;
  } | null>(null);

  useEffect(() => {
    if (isEnterpriseEnabled()) {
      Promise.all([
        import("@/ee/auth/components/AuthGuard"),
        import("@/ee/auth/components/UserMenu"),
      ]).then(([authGuard, userMenu]) => {
        setEEComponents({
          AuthGuard: authGuard.AuthGuard,
          UserMenu: userMenu.UserMenu,
        });
      });
    }
  }, []);

  // ... rest of component
}
```

Also set up the Axios interceptor when EE is enabled:

```tsx
useEffect(() => {
  if (isEnterpriseEnabled()) {
    import("@/ee/auth/lib/axios-interceptor").then(({ authRequestInterceptor }) => {
      const { OpenAPI } = require("@/lib/api");
      // Or set up axios default interceptor
      import("axios").then(({ default: axios }) => {
        axios.interceptors.request.use(authRequestInterceptor);
      });
    });
  }
}, []);
```

**Step 2: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(ee): integrate auth into App.tsx with conditional loading"
```

---

## Task 11: Update .env.example and cleanup

**Files:**
- Modify: `.env.example` (if not done in Task 3)
- Remove: `.gitkeep` files created in Task 1 (now replaced by real files)

**Step 1: Remove .gitkeep files**

Remove any `.gitkeep` files from `frontend/src/ee/` subdirectories that now contain real files.

**Step 2: Commit**

```bash
git add -A
git commit -m "chore(ee): cleanup gitkeep files"
```

---

## Task 12: Verify EE-disabled mode (OSS regression check)

**Step 1: Ensure ENTERPRISE_ENABLED is not set (or false)**

```bash
# Verify no ENTERPRISE_ENABLED in .env or it's set to false
grep ENTERPRISE_ENABLED .env
```

**Step 2: Start backend and verify existing endpoints work**

```bash
cd backend && uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Step 3: Verify EE routes are NOT registered**

```bash
curl http://localhost:8000/airas/ee/auth/me
# Expected: 404 (route not found)
```

**Step 4: Verify existing endpoints still work**

```bash
curl http://localhost:8000/docs
# Expected: 200 with Swagger docs, no EE routes listed
```

**Step 5: Start frontend and verify no login gate**

```bash
cd frontend && npm run dev
# Visit http://localhost:5173 — should show app directly without login
```

---

## Dependency Order

```
Task 1 (scaffold) → Task 2 (deps) → Task 3 (settings)
  → Task 4 (JWT middleware) → Task 5 (auth routes)
  → Task 6 (frontend deps) → Task 7 (supabase client) → Task 8 (auth components)
  → Task 9 (axios interceptor) → Task 10 (App.tsx integration)
  → Task 11 (cleanup) → Task 12 (regression check)
```

Backend tasks (1-5) and frontend tasks (6-10) can be parallelized after Task 3.
