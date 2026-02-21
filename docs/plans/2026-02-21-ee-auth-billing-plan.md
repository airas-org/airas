# EE Auth & Billing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add enterprise authentication (Supabase Auth) and billing (Stripe Subscription) to AIRAS under `ee/` directories with ELv2 license, keeping OSS behavior unchanged.

**Architecture:** Frontend uses Supabase JS SDK for OAuth login (Google/GitHub), backend verifies JWT with PyJWT. Stripe Checkout handles payments, Stripe Webhooks sync subscription state to PostgreSQL. `ENTERPRISE_ENABLED` env var toggles the entire EE stack on/off.

**Tech Stack:** Supabase Auth, Stripe, PyJWT, FastAPI, React, Axios, SQLModel

---

## Task 1: EE directory scaffolding and licenses

**Files:**
- Create: `frontend/src/ee/LICENSE`
- Create: `backend/api/ee/__init__.py`
- Create: `backend/api/ee/LICENSE`
- Create: `backend/api/ee/auth/__init__.py`
- Create: `backend/api/ee/billing/__init__.py`
- Create: `frontend/src/ee/config.ts`
- Create: `frontend/src/ee/auth/lib/.gitkeep`
- Create: `frontend/src/ee/auth/hooks/.gitkeep`
- Create: `frontend/src/ee/auth/components/.gitkeep`
- Create: `frontend/src/ee/billing/lib/.gitkeep`
- Create: `frontend/src/ee/billing/hooks/.gitkeep`
- Create: `frontend/src/ee/billing/components/.gitkeep`

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

## Task 2: Backend — Add PyJWT and stripe dependencies

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add dependencies to pyproject.toml**

Add to the `[project.dependencies]` section:

```toml
"PyJWT[crypto]>=2.8.0",
"stripe>=8.0.0",
```

**Step 2: Install dependencies**

```bash
cd backend && uv sync
```

**Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "feat(ee): add PyJWT and stripe dependencies"
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
    stripe_api_key: str
    stripe_webhook_secret: str


def get_ee_settings() -> EESettings:
    return EESettings(
        enabled=os.getenv("ENTERPRISE_ENABLED", "false").lower() == "true",
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
        stripe_api_key=os.getenv("STRIPE_API_KEY", ""),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", ""),
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
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
VITE_ENTERPRISE_ENABLED=false
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_STRIPE_PUBLISHABLE_KEY=
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
    from api.ee.billing.routes import router as ee_billing_router

    app.include_router(ee_auth_router, prefix="/airas/ee")
    app.include_router(ee_billing_router, prefix="/airas/ee")
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

## Task 6: Backend — Subscription database model

**Files:**
- Create: `backend/api/ee/billing/models.py`

**Step 1: Create SubscriptionModel**

```python
# backend/api/ee/billing/models.py
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Column, Enum, Field, SQLModel


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class SubscriptionModel(SQLModel, table=True):
    __tablename__ = "subscriptions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True, nullable=False)
    stripe_customer_id: str = Field(index=True, nullable=False)
    stripe_subscription_id: str | None = Field(default=None, index=True)
    plan: PlanType = Field(
        sa_column=Column(Enum(PlanType), nullable=False, default=PlanType.FREE)
    )
    status: SubscriptionStatus = Field(
        sa_column=Column(
            Enum(SubscriptionStatus),
            nullable=False,
            default=SubscriptionStatus.INCOMPLETE,
        )
    )
    current_period_start: datetime | None = Field(default=None)
    current_period_end: datetime | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

**Step 2: Commit**

```bash
git add backend/api/ee/billing/models.py
git commit -m "feat(ee): add Subscription database model"
```

---

## Task 7: Backend — Stripe billing service

**Files:**
- Create: `backend/api/ee/billing/service.py`

**Step 1: Create Stripe service**

```python
# backend/api/ee/billing/service.py
from datetime import datetime, timezone
from uuid import UUID

import stripe
from sqlmodel import Session, select

from api.ee.billing.models import PlanType, SubscriptionModel, SubscriptionStatus
from api.ee.settings import get_ee_settings


def _init_stripe() -> None:
    settings = get_ee_settings()
    stripe.api_key = settings.stripe_api_key


def create_checkout_session(
    user_id: UUID,
    price_id: str,
    success_url: str,
    cancel_url: str,
    db: Session,
) -> str:
    """Create a Stripe Checkout session and return the URL."""
    _init_stripe()

    # Find or create Stripe customer
    sub = db.exec(
        select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
    ).first()

    if sub and sub.stripe_customer_id:
        customer_id = sub.stripe_customer_id
    else:
        customer = stripe.Customer.create(metadata={"user_id": str(user_id)})
        customer_id = customer.id
        if not sub:
            sub = SubscriptionModel(
                user_id=user_id,
                stripe_customer_id=customer_id,
                plan=PlanType.FREE,
                status=SubscriptionStatus.INCOMPLETE,
            )
            db.add(sub)
            db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_portal_session(user_id: UUID, return_url: str, db: Session) -> str:
    """Create a Stripe Billing Portal session and return the URL."""
    _init_stripe()
    sub = db.exec(
        select(SubscriptionModel).where(SubscriptionModel.user_id == user_id)
    ).first()
    if not sub or not sub.stripe_customer_id:
        raise ValueError("No subscription found for user")

    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> None:
    """Process a Stripe webhook event."""
    settings = get_ee_settings()
    _init_stripe()

    event = stripe.Webhook.construct_event(
        payload, sig_header, settings.stripe_webhook_secret
    )

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] in (
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        _handle_subscription_change(event["data"]["object"], db)


def _handle_checkout_completed(session: dict, db: Session) -> None:
    customer_id = session["customer"]
    subscription_id = session["subscription"]

    sub = db.exec(
        select(SubscriptionModel).where(
            SubscriptionModel.stripe_customer_id == customer_id
        )
    ).first()
    if sub:
        sub.stripe_subscription_id = subscription_id
        sub.status = SubscriptionStatus.ACTIVE
        sub.plan = PlanType.PRO
        sub.updated_at = datetime.now(timezone.utc)
        db.add(sub)
        db.commit()


def _handle_subscription_change(subscription: dict, db: Session) -> None:
    subscription_id = subscription["id"]
    status_str = subscription["status"]

    sub = db.exec(
        select(SubscriptionModel).where(
            SubscriptionModel.stripe_subscription_id == subscription_id
        )
    ).first()
    if not sub:
        return

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "trialing": SubscriptionStatus.TRIALING,
    }
    sub.status = status_map.get(status_str, SubscriptionStatus.INCOMPLETE)

    period_start = subscription.get("current_period_start")
    period_end = subscription.get("current_period_end")
    if period_start:
        sub.current_period_start = datetime.fromtimestamp(
            period_start, tz=timezone.utc
        )
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    if status_str == "canceled":
        sub.plan = PlanType.FREE

    sub.updated_at = datetime.now(timezone.utc)
    db.add(sub)
    db.commit()
```

**Step 2: Commit**

```bash
git add backend/api/ee/billing/service.py
git commit -m "feat(ee): add Stripe billing service"
```

---

## Task 8: Backend — Billing routes

**Files:**
- Create: `backend/api/ee/billing/routes.py`

**Step 1: Create billing routes**

```python
# backend/api/ee/billing/routes.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from api.ee.auth.dependencies import get_current_user_id
from api.ee.billing.service import (
    create_checkout_session,
    create_portal_session,
    handle_webhook_event,
)

router = APIRouter(prefix="/billing", tags=["ee-billing"])


class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str


class PortalRequest(BaseModel):
    return_url: str


class PortalResponse(BaseModel):
    url: str


def _get_db(request: Request) -> Session:
    """Get database session from container."""
    container = request.app.state.container
    return container.session_factory()


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(_get_db),
):
    url = create_checkout_session(
        user_id=user_id,
        price_id=body.price_id,
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        db=db,
    )
    if not url:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")
    return CheckoutResponse(url=url)


@router.post("/create-portal-session", response_model=PortalResponse)
async def create_portal(
    body: PortalRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(_get_db),
):
    try:
        url = create_portal_session(
            user_id=user_id,
            return_url=body.return_url,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PortalResponse(url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(_get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    try:
        handle_webhook_event(payload, sig_header, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}
```

**Step 2: Commit**

```bash
git add backend/api/ee/billing/routes.py
git commit -m "feat(ee): add billing routes (checkout, portal, webhook)"
```

---

## Task 9: Frontend — Add Supabase dependency and EE config

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

## Task 10: Frontend — Supabase client and auth hooks

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

## Task 11: Frontend — Auth components (LoginPage, AuthGuard, AuthCallback, UserMenu)

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

## Task 12: Frontend — Axios interceptor for JWT

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

## Task 13: Frontend — Integrate EE into App.tsx

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

## Task 14: Frontend — Billing components

**Files:**
- Create: `frontend/src/ee/billing/hooks/useSubscription.ts`
- Create: `frontend/src/ee/billing/components/PricingPage.tsx`
- Create: `frontend/src/ee/billing/components/BillingPortal.tsx`
- Create: `frontend/src/ee/billing/components/PlanBadge.tsx`

**Step 1: Create useSubscription hook**

```typescript
// frontend/src/ee/billing/hooks/useSubscription.ts
import { useCallback, useEffect, useState } from "react";
import axios from "axios";

interface Subscription {
  plan: "free" | "pro" | "enterprise";
  status: "active" | "canceled" | "past_due" | "incomplete" | "trialing";
}

export function useSubscription() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSubscription = useCallback(async () => {
    try {
      const res = await axios.get("/airas/ee/billing/subscription");
      setSubscription(res.data);
    } catch {
      setSubscription(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubscription();
  }, [fetchSubscription]);

  return { subscription, loading, refetch: fetchSubscription };
}
```

**Step 2: Create PricingPage**

```tsx
// frontend/src/ee/billing/components/PricingPage.tsx
import axios from "axios";

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["Basic research", "Community support"],
    priceId: null,
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    features: ["Unlimited research", "Priority support", "Advanced analytics"],
    priceId: "price_pro_monthly", // Replace with actual Stripe price ID
  },
];

export function PricingPage() {
  const handleCheckout = async (priceId: string) => {
    const res = await axios.post("/airas/ee/billing/create-checkout-session", {
      price_id: priceId,
      success_url: `${window.location.origin}/?checkout=success`,
      cancel_url: `${window.location.origin}/?checkout=canceled`,
    });
    window.location.href = res.data.url;
  };

  return (
    <div className="mx-auto max-w-3xl p-8">
      <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
        Choose your plan
      </h2>
      <div className="grid grid-cols-2 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className="rounded-lg border border-border bg-card p-6 space-y-4"
          >
            <h3 className="text-lg font-semibold">{plan.name}</h3>
            <div className="text-3xl font-bold">
              {plan.price}
              <span className="text-sm font-normal text-muted-foreground">
                {plan.period}
              </span>
            </div>
            <ul className="space-y-2 text-sm text-muted-foreground">
              {plan.features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
            {plan.priceId && (
              <button
                type="button"
                onClick={() => handleCheckout(plan.priceId!)}
                className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Subscribe
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 3: Create BillingPortal**

```tsx
// frontend/src/ee/billing/components/BillingPortal.tsx
import axios from "axios";

export function BillingPortal() {
  const handlePortal = async () => {
    const res = await axios.post("/airas/ee/billing/create-portal-session", {
      return_url: window.location.origin,
    });
    window.location.href = res.data.url;
  };

  return (
    <button
      type="button"
      onClick={handlePortal}
      className="rounded-md border border-border px-4 py-2 text-sm text-foreground hover:bg-muted/60 transition-colors"
    >
      Manage subscription
    </button>
  );
}
```

**Step 4: Create PlanBadge**

```tsx
// frontend/src/ee/billing/components/PlanBadge.tsx
import { cn } from "@/lib/utils";

interface PlanBadgeProps {
  plan: "free" | "pro" | "enterprise";
}

export function PlanBadge({ plan }: PlanBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        plan === "pro" && "bg-blue-100 text-blue-800",
        plan === "enterprise" && "bg-purple-100 text-purple-800",
        plan === "free" && "bg-gray-100 text-gray-800",
      )}
    >
      {plan.charAt(0).toUpperCase() + plan.slice(1)}
    </span>
  );
}
```

**Step 5: Commit**

```bash
git add frontend/src/ee/billing/
git commit -m "feat(ee): add billing components (PricingPage, BillingPortal, PlanBadge)"
```

---

## Task 15: Update .env.example and cleanup

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

## Task 16: Verify EE-disabled mode (OSS regression check)

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
  → Task 6 (subscription model) → Task 7 (billing service) → Task 8 (billing routes)
  → Task 9 (frontend deps) → Task 10 (supabase client) → Task 11 (auth components)
  → Task 12 (axios interceptor) → Task 13 (App.tsx integration)
  → Task 14 (billing components)
  → Task 15 (cleanup) → Task 16 (regression check)
```

Backend tasks (1-8) and frontend tasks (9-14) can be parallelized after Task 3.
