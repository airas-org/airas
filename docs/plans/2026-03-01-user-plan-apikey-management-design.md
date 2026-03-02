# ユーザープラン・APIキー管理 実装計画

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 無料版/Pro版のプラン管理、APIキー暗号化保存、Stripe Checkout連携、フロントエンドのIntegration/UserPlanページを実装する。

**Architecture:** 既存の `api/ee/` パッケージ配下にプラン管理・APIキー管理・Stripe連携を追加するモノリシック実装。フロントエンドは既存のSettingsページを廃止し、IntegrationとUser Planの2つの独立トップレベルページに分割。

**Tech Stack:** FastAPI, SQLModel, AES-256-GCM (cryptography), Stripe SDK, React, Tailwind CSS, lucide-react

---

## Task 1: バックエンド依存パッケージ追加

**Files:**
- Modify: `backend/pyproject.toml:48` (dependencies セクション)

**Step 1: パッケージ追加**

`backend/pyproject.toml` の `dependencies` リストに以下を追加:

```toml
    "cryptography>=44.0.0",
    "stripe>=12.0.0",
```

**Step 2: インストール確認**

Run: `cd /workspaces/airas/backend && uv sync`
Expected: 正常にインストール完了

**Step 3: コミット**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "chore: cryptographyとstripeパッケージを追加"
```

---

## Task 2: AES-256-GCM 暗号化モジュール

**Files:**
- Create: `backend/src/airas/infra/encryption.py`

**Step 1: 暗号化モジュール実装**

```python
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_key() -> bytes:
    key_b64 = os.getenv("API_KEY_ENCRYPTION_KEY", "")
    if not key_b64:
        raise RuntimeError("API_KEY_ENCRYPTION_KEY environment variable is not set")
    return base64.b64decode(key_b64)


def encrypt(plaintext: str) -> str:
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(token: str) -> str:
    key = _get_key()
    raw = base64.b64decode(token)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
```

**Step 2: コミット**

```bash
git add backend/src/airas/infra/encryption.py
git commit -m "feat: AES-256-GCM暗号化モジュールを追加"
```

---

## Task 3: DBモデル (UserApiKey, UserPlan)

**Files:**
- Create: `backend/src/airas/infra/db/models/user_api_key.py`
- Create: `backend/src/airas/infra/db/models/user_plan.py`

**Step 1: UserApiKeyモデル**

```python
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlmodel import Field, SQLModel


class ApiProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"


class UserApiKeyModel(SQLModel, table=True):
    __tablename__ = "user_api_keys"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_api_key_provider"),
        Index("ix_user_api_keys_user_id", "user_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(nullable=False)
    provider: ApiProvider = Field(sa_column=Column(String, nullable=False))
    encrypted_key: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "now()"},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"server_default": "now()"},
    )
```

**Step 2: UserPlanモデル**

```python
import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String
from sqlmodel import Field, SQLModel


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class UserPlanModel(SQLModel, table=True):
    __tablename__ = "user_plans"
    __table_args__ = (Index("ix_user_plans_user_id", "user_id", unique=True),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(nullable=False, unique=True)
    plan_type: PlanType = Field(
        default=PlanType.FREE, sa_column=Column(String, nullable=False, server_default="free")
    )
    stripe_customer_id: str | None = Field(default=None)
    stripe_subscription_id: str | None = Field(default=None)
    status: PlanStatus = Field(
        default=PlanStatus.ACTIVE,
        sa_column=Column(String, nullable=False, server_default="active"),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
```

**Step 3: コミット**

```bash
git add backend/src/airas/infra/db/models/user_api_key.py backend/src/airas/infra/db/models/user_plan.py
git commit -m "feat: UserApiKeyとUserPlanのDBモデルを追加"
```

---

## Task 4: リポジトリ層 (UserApiKey, UserPlan)

**Files:**
- Create: `backend/src/airas/repository/user_api_key_repository.py`
- Create: `backend/src/airas/repository/user_plan_repository.py`

**Step 1: UserApiKeyRepository**

```python
from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_api_key import ApiProvider, UserApiKeyModel
from airas.repository.base_repository import BaseRepository


class UserApiKeyRepository(BaseRepository[UserApiKeyModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserApiKeyModel)

    def get_by_user_and_provider(
        self, user_id: UUID, provider: ApiProvider
    ) -> UserApiKeyModel | None:
        stmt = select(UserApiKeyModel).where(
            UserApiKeyModel.user_id == user_id,
            UserApiKeyModel.provider == provider,
        )
        return self.db.exec(stmt).first()

    def list_by_user(self, user_id: UUID) -> list[UserApiKeyModel]:
        stmt = select(UserApiKeyModel).where(UserApiKeyModel.user_id == user_id)
        return self.db.exec(stmt).all()

    def delete_by_user_and_provider(self, user_id: UUID, provider: ApiProvider) -> bool:
        obj = self.get_by_user_and_provider(user_id, provider)
        if obj is None:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
```

**Step 2: UserPlanRepository**

```python
from uuid import UUID

from sqlmodel import Session, select

from airas.infra.db.models.user_plan import UserPlanModel
from airas.repository.base_repository import BaseRepository


class UserPlanRepository(BaseRepository[UserPlanModel]):
    def __init__(self, db: Session):
        super().__init__(db, UserPlanModel)

    def get_by_user(self, user_id: UUID) -> UserPlanModel | None:
        stmt = select(UserPlanModel).where(UserPlanModel.user_id == user_id)
        return self.db.exec(stmt).first()
```

**Step 3: コミット**

```bash
git add backend/src/airas/repository/user_api_key_repository.py backend/src/airas/repository/user_plan_repository.py
git commit -m "feat: UserApiKeyとUserPlanのリポジトリを追加"
```

---

## Task 5: サービス層 (ApiKeyService, PlanService)

**Files:**
- Create: `backend/src/airas/usecases/ee/api_key_service.py`
- Create: `backend/src/airas/usecases/ee/plan_service.py`
- Create: `backend/src/airas/usecases/ee/__init__.py`

**Step 1: ApiKeyService**

```python
from datetime import datetime, timezone
from uuid import UUID

from airas.infra.db.models.user_api_key import ApiProvider, UserApiKeyModel
from airas.infra.encryption import decrypt, encrypt
from airas.repository.user_api_key_repository import UserApiKeyRepository


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


class ApiKeyService:
    def __init__(self, repo: UserApiKeyRepository):
        self.repo = repo

    def save_key(self, *, user_id: UUID, provider: ApiProvider, api_key: str) -> UserApiKeyModel:
        existing = self.repo.get_by_user_and_provider(user_id, provider)
        if existing:
            existing.encrypted_key = encrypt(api_key)
            existing.updated_at = datetime.now(timezone.utc)
            self.repo.db.add(existing)
            self.repo.db.commit()
            self.repo.db.refresh(existing)
            return existing
        model = UserApiKeyModel(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypt(api_key),
        )
        return self.repo.create(model)

    def list_keys(self, user_id: UUID) -> list[dict]:
        keys = self.repo.list_by_user(user_id)
        return [
            {
                "provider": k.provider,
                "masked_key": _mask_key(decrypt(k.encrypted_key)),
                "created_at": k.created_at,
                "updated_at": k.updated_at,
            }
            for k in keys
        ]

    def delete_key(self, *, user_id: UUID, provider: ApiProvider) -> bool:
        return self.repo.delete_by_user_and_provider(user_id, provider)

    def close(self) -> None:
        self.repo.db.close()
```

**Step 2: PlanService**

```python
import os
from uuid import UUID

import stripe

from airas.infra.db.models.user_plan import PlanStatus, PlanType, UserPlanModel
from airas.repository.user_plan_repository import UserPlanRepository


class PlanService:
    def __init__(self, repo: UserPlanRepository):
        self.repo = repo
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    def get_plan(self, user_id: UUID) -> UserPlanModel:
        plan = self.repo.get_by_user(user_id)
        if plan is None:
            plan = UserPlanModel(user_id=user_id, plan_type=PlanType.FREE, status=PlanStatus.ACTIVE)
            return self.repo.create(plan)
        return plan

    def create_checkout_session(self, *, user_id: UUID, success_url: str, cancel_url: str) -> str:
        plan = self.get_plan(user_id)
        price_id = os.getenv("STRIPE_PRO_PRICE_ID", "")

        customer_id = plan.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(metadata={"user_id": str(user_id)})
            customer_id = customer.id
            plan.stripe_customer_id = customer_id
            self.repo.db.add(plan)
            self.repo.db.commit()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url or ""

    def handle_webhook_event(self, event: dict) -> None:
        event_type = event.get("type", "")
        data_obj = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            customer_id = data_obj.get("customer", "")
            subscription_id = data_obj.get("subscription", "")
            self._activate_pro(customer_id, subscription_id)
        elif event_type == "customer.subscription.deleted":
            customer_id = data_obj.get("customer", "")
            self._deactivate_pro(customer_id)

    def _activate_pro(self, customer_id: str, subscription_id: str) -> None:
        from sqlmodel import select
        stmt = select(UserPlanModel).where(UserPlanModel.stripe_customer_id == customer_id)
        plan = self.repo.db.exec(stmt).first()
        if plan:
            plan.plan_type = PlanType.PRO
            plan.stripe_subscription_id = subscription_id
            plan.status = PlanStatus.ACTIVE
            self.repo.db.add(plan)
            self.repo.db.commit()

    def _deactivate_pro(self, customer_id: str) -> None:
        from sqlmodel import select
        stmt = select(UserPlanModel).where(UserPlanModel.stripe_customer_id == customer_id)
        plan = self.repo.db.exec(stmt).first()
        if plan:
            plan.plan_type = PlanType.FREE
            plan.status = PlanStatus.CANCELED
            self.repo.db.add(plan)
            self.repo.db.commit()

    def close(self) -> None:
        self.repo.db.close()
```

**Step 3: コミット**

```bash
git add backend/src/airas/usecases/ee/
git commit -m "feat: ApiKeyServiceとPlanServiceを追加"
```

---

## Task 6: DI Container にサービス登録

**Files:**
- Modify: `backend/src/airas/container.py`

**Step 1: import追加 (ファイル先頭)**

`container.py` に以下のimportを追加:

```python
from airas.repository.user_api_key_repository import UserApiKeyRepository
from airas.repository.user_plan_repository import UserPlanRepository
from airas.usecases.ee.api_key_service import ApiKeyService
from airas.usecases.ee.plan_service import PlanService
```

**Step 2: Container クラスに以下を追加 (e2e_research_service の後)**

```python
    # --- EE: API Key & Plan Services ---
    user_api_key_repository = providers.Factory(
        UserApiKeyRepository, db=db_session
    )
    api_key_service = providers.Factory(
        ApiKeyService, repo=user_api_key_repository
    )

    user_plan_repository = providers.Factory(
        UserPlanRepository, db=db_session
    )
    plan_service = providers.Factory(
        PlanService, repo=user_plan_repository
    )
```

**Step 3: コミット**

```bash
git add backend/src/airas/container.py
git commit -m "feat: DI ContainerにAPIキー・プランサービスを登録"
```

---

## Task 7: バックエンド APIルート

**Files:**
- Create: `backend/api/ee/api_keys/routes.py`
- Create: `backend/api/ee/api_keys/__init__.py`
- Create: `backend/api/ee/plan/routes.py`
- Create: `backend/api/ee/plan/__init__.py`
- Create: `backend/api/ee/stripe/routes.py`
- Create: `backend/api/ee/stripe/__init__.py`
- Create: `backend/api/schemas/ee.py`
- Modify: `backend/api/main.py` (ルーター登録)

**Step 1: スキーマ定義** (`backend/api/schemas/ee.py`)

```python
from datetime import datetime

from pydantic import BaseModel

from airas.infra.db.models.user_api_key import ApiProvider


class SaveApiKeyRequest(BaseModel):
    provider: ApiProvider
    api_key: str


class ApiKeyResponse(BaseModel):
    provider: ApiProvider
    masked_key: str
    created_at: datetime
    updated_at: datetime


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyResponse]


class UserPlanResponse(BaseModel):
    plan_type: str
    status: str
    stripe_customer_id: str | None = None


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
```

**Step 2: APIキー ルート** (`backend/api/ee/api_keys/routes.py`)

```python
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import ApiKeyListResponse, ApiKeyResponse, SaveApiKeyRequest
from airas.container import Container
from airas.infra.db.models.user_api_key import ApiProvider
from airas.usecases.ee.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys", tags=["ee-api-keys"])


@router.post("", response_model=ApiKeyResponse)
@inject
def save_api_key(
    request: SaveApiKeyRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
) -> ApiKeyResponse:
    model = service.save_key(
        user_id=current_user_id, provider=request.provider, api_key=request.api_key
    )
    keys = service.list_keys(current_user_id)
    matched = next(k for k in keys if k["provider"] == request.provider)
    return ApiKeyResponse(**matched)


@router.get("", response_model=ApiKeyListResponse)
@inject
def list_api_keys(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
) -> ApiKeyListResponse:
    return ApiKeyListResponse(keys=service.list_keys(current_user_id))


@router.delete("/{provider}")
@inject
def delete_api_key(
    provider: ApiProvider,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[ApiKeyService, Depends(Provide[Container.api_key_service])],
):
    deleted = service.delete_key(user_id=current_user_id, provider=provider)
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API key not found")
    return {"deleted": True}
```

**Step 3: プラン ルート** (`backend/api/ee/plan/routes.py`)

```python
from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import UserPlanResponse
from airas.container import Container
from airas.usecases.ee.plan_service import PlanService

router = APIRouter(prefix="/plan", tags=["ee-plan"])


@router.get("", response_model=UserPlanResponse)
@inject
def get_plan(
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[PlanService, Depends(Provide[Container.plan_service])],
) -> UserPlanResponse:
    plan = service.get_plan(current_user_id)
    return UserPlanResponse(
        plan_type=plan.plan_type,
        status=plan.status,
        stripe_customer_id=plan.stripe_customer_id,
    )
```

**Step 4: Stripe ルート** (`backend/api/ee/stripe/routes.py`)

```python
import os
from typing import Annotated
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from api.ee.auth.dependencies import get_current_user_id
from api.schemas.ee import CheckoutRequest, CheckoutResponse
from airas.container import Container
from airas.usecases.ee.plan_service import PlanService
from dependency_injector.wiring import Provide, inject

router = APIRouter(prefix="/stripe", tags=["ee-stripe"])


@router.post("/checkout", response_model=CheckoutResponse)
@inject
def create_checkout(
    request: CheckoutRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user_id)],
    service: Annotated[PlanService, Depends(Provide[Container.plan_service])],
) -> CheckoutResponse:
    url = service.create_checkout_session(
        user_id=current_user_id,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    from sqlmodel import Session, create_engine
    database_url = os.getenv("DATABASE_URL", "")
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(database_url)
    with Session(engine) as session:
        from airas.repository.user_plan_repository import UserPlanRepository
        repo = UserPlanRepository(db=session)
        plan_service = PlanService(repo=repo)
        plan_service.handle_webhook_event(event)

    return {"received": True}
```

**Step 5: main.py にルーター登録**

`backend/api/main.py` の EE routes 登録部分（line 115-119 付近）に追加:

```python
if _ee_settings.enabled:
    from api.ee.auth.routes import router as ee_auth_router
    from api.ee.api_keys.routes import router as ee_api_keys_router
    from api.ee.plan.routes import router as ee_plan_router
    from api.ee.stripe.routes import router as ee_stripe_router

    app.include_router(ee_auth_router, prefix="/airas/ee")
    app.include_router(ee_api_keys_router, prefix="/airas/ee")
    app.include_router(ee_plan_router, prefix="/airas/ee")
    app.include_router(ee_stripe_router, prefix="/airas/ee")
```

**Step 6: コミット**

```bash
git add backend/api/ee/ backend/api/schemas/ee.py backend/api/main.py
git commit -m "feat: APIキー・プラン・Stripeのルートを追加"
```

---

## Task 8: フロントエンド — Integration ページ

**Files:**
- Create: `frontend/src/components/pages/integration.tsx`

**Step 1: Integrationページ実装**

GitHub Integration セクション（既存settings内容）＋ APIキー設定フォームを含むページ。
- プロバイダーごと（OpenAI, Anthropic, Gemini）のAPIキー入力フォーム
- 保存済みキーはマスク表示
- 保存・削除ボタン
- `GET /airas/ee/api-keys` と `POST /airas/ee/api-keys` と `DELETE /airas/ee/api-keys/{provider}` を呼び出し

**Step 2: コミット**

```bash
git add frontend/src/components/pages/integration.tsx
git commit -m "feat: Integrationページを追加"
```

---

## Task 9: フロントエンド — User Plan ページ

**Files:**
- Create: `frontend/src/components/pages/user-plan.tsx`

**Step 1: UserPlanページ実装**

- Free / Pro プランを縦に並べた比較表
- 現在のプランはボーダーハイライト + 「Current Plan」バッジ
- 非アクティブプランには「プランを変更」ボタン
- 「プランを変更」ボタンは `POST /airas/ee/stripe/checkout` を呼び出し、返却された `checkout_url` に遷移
- `GET /airas/ee/plan` でユーザーの現在のプランを取得

**Step 2: コミット**

```bash
git add frontend/src/components/pages/user-plan.tsx
git commit -m "feat: User Planページを追加"
```

---

## Task 10: フロントエンド — ナビゲーション変更 + UserMenu拡張

**Files:**
- Modify: `frontend/src/components/main-content.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/ee/auth/components/UserMenu.tsx`
- Delete: `frontend/src/components/pages/settings.tsx`

**Step 1: NavKey型を更新** (`main-content.tsx:16`)

```typescript
export type NavKey = "papers" | "assisted-research" | "autonomous-research" | "integration" | "user-plan";
```

**Step 2: MainContentにIntegrationとUserPlanを追加**

`main-content.tsx` のSettingsPage import を IntegrationPage と UserPlanPage に置換し、レンダリング部分を変更:

```tsx
// 削除: import { SettingsPage } from "@/components/pages/settings";
import { IntegrationPage } from "@/components/pages/integration";
import { UserPlanPage } from "@/components/pages/user-plan";

// renderの settings 部分を以下に置換:
<div className={activeNav === "integration" ? "flex-1 flex" : "hidden"}>
  <IntegrationPage />
</div>
<div className={activeNav === "user-plan" ? "flex-1 flex" : "hidden"}>
  <UserPlanPage />
</div>
```

**Step 3: App.tsxのサイドバー変更**

Settings ボタン（lines 445-456）を Integration と User Plan の2つのボタンに置換:

```tsx
<button
  type="button"
  onClick={() => handleNavChange("integration")}
  className={cn(
    "w-full px-3 py-1.5 text-left text-sm transition-colors border-l-2 cursor-pointer",
    activeNav === "integration"
      ? "text-foreground font-semibold border-blue-700"
      : "text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent",
  )}
>
  Integration
</button>
<button
  type="button"
  onClick={() => handleNavChange("user-plan")}
  className={cn(
    "w-full px-3 py-1.5 text-left text-sm transition-colors border-l-2 cursor-pointer",
    activeNav === "user-plan"
      ? "text-foreground font-semibold border-blue-700"
      : "text-muted-foreground hover:text-foreground hover:bg-muted/40 border-transparent",
  )}
>
  User Plan
</button>
```

**Step 4: SectionsSidebar の表示条件を更新** (`App.tsx:460`)

Integration と User Plan では SectionsSidebar を表示しないため、条件はそのままでOK（`assisted-research` と `autonomous-research` のみ表示）。

**Step 5: UserMenu にプラン表示を追加** (`UserMenu.tsx`)

email表示の下にプランバッジを追加:

```tsx
// メールの下に追加
<div className="px-3 py-1.5 border-b border-border">
  <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-200">
    {plan ?? "Free"}
  </span>
</div>
```

プラン情報は `GET /airas/ee/plan` で取得。useEffect で取得してstateに保存。

**Step 6: settings.tsx を削除**

**Step 7: コミット**

```bash
git add frontend/src/components/main-content.tsx frontend/src/App.tsx frontend/src/ee/auth/components/UserMenu.tsx
git rm frontend/src/components/pages/settings.tsx
git commit -m "feat: ナビゲーションをIntegration/UserPlanに変更し、UserMenuにプラン表示を追加"
```

---

## Task 11: ビルド確認 + 最終コミット

**Step 1: バックエンド lint/type check**

Run: `cd /workspaces/airas && make ruff && make mypy`

**Step 2: フロントエンド lint + build**

Run: `cd /workspaces/airas && make biome`
Run: `cd /workspaces/airas/frontend && npx tsc --noEmit`

**Step 3: 問題があれば修正してコミット**

---

## チーム分担

| Task | 担当エージェント | 依存関係 |
|------|--------------|---------|
| Task 1-2 | backend-engineer | なし |
| Task 3-4 | backend-engineer | Task 1 |
| Task 5-6 | backend-engineer | Task 3-4 |
| Task 7 | backend-engineer | Task 5-6 |
| Task 8 | frontend-engineer | なし (APIはモックでも可) |
| Task 9 | frontend-engineer | なし (APIはモックでも可) |
| Task 10 | frontend-engineer | Task 8-9 |
| Task 11 | team-lead | Task 7, 10 |

**並行可能:** backend (Task 1-7) と frontend (Task 8-10) は並行作業可能。
