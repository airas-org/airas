# Enterprise Edition: Auth & Billing Design

## Overview

AIRAS にエンタープライズ向けの認証（Supabase Auth）と課金（Stripe Subscription）を追加する。
OSS版は現状の動作を維持し、`ee/` ディレクトリに ELv2 ライセンスで分離する。

## 決定事項

- **認証**: Supabase Auth（ソーシャルログインのみ: Google + GitHub）
- **課金**: Stripe サブスクリプション（月額/年額）
- **アクセス制御**: EE有効時は全機能ログイン必須
- **ライセンス**: `ee/` ディレクトリに Elastic License v2 (ELv2)
- **アプローチ**: フロントエンドで Supabase SDK 直接統合、バックエンドで JWT 検証

## ディレクトリ構成

```
frontend/src/
├── ee/
│   ├── LICENSE                  # Elastic License v2
│   ├── config.ts                # isEnterpriseEnabled()
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── AuthGuard.tsx
│   │   │   ├── AuthCallback.tsx
│   │   │   └── UserMenu.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useSession.ts
│   │   └── lib/
│   │       └── supabase.ts
│   └── billing/
│       ├── components/
│       │   ├── PricingPage.tsx
│       │   ├── BillingPortal.tsx
│       │   └── PlanBadge.tsx
│       ├── hooks/
│       │   └── useSubscription.ts
│       └── lib/

backend/api/
├── ee/
│   ├── LICENSE                  # Elastic License v2
│   ├── auth/
│   │   ├── middleware.py        # JWT検証ミドルウェア
│   │   ├── dependencies.py     # get_current_user (FastAPI Depends)
│   │   └── routes.py           # /ee/auth/* エンドポイント
│   └── billing/
│       ├── routes.py            # /ee/billing/* エンドポイント
│       ├── models.py            # SubscriptionModel
│       └── service.py           # Stripe連携ロジック
```

## EE有効/無効の切り替え

環境変数 `ENTERPRISE_ENABLED` (バックエンド) / `VITE_ENTERPRISE_ENABLED` (フロントエンド) で制御。

### OSS利用時（デフォルト）

- `ENTERPRISE_ENABLED=false`
- 認証スキップ、固定ユーザーID (`SYSTEM_USER_ID`)
- EEルートは登録されない
- 全機能が無料でそのまま使える（現状と同じ動作）

### エンタープライズ利用時

- `ENTERPRISE_ENABLED=true`
- ログイン必須、JWTでユーザー特定
- サブスクリプション課金が有効

## バックエンド設計

### 認証

- `get_current_user_id()` の分岐: EE有効時は JWT 検証、無効時は `SYSTEM_USER_ID`
- Supabase JWT の署名検証・有効期限チェック（`PyJWT` 使用）
- 認証の実体は Supabase 側。バックエンドは JWT 検証のみ

### 課金

- `POST /ee/billing/create-checkout-session` — Stripe Checkout セッション作成
- `POST /ee/billing/create-portal-session` — Stripe Billing Portal 遷移
- `POST /ee/billing/webhook` — Stripe Webhook 受信・サブスク状態同期
- `SubscriptionModel` — user_id, stripe_customer_id, plan, status, 期間を DB 保存
- `require_active_subscription()` — 有料プラン必須エンドポイント用 Dependency

### 追加パッケージ

- `PyJWT` — JWT検証
- `stripe` — Stripe API SDK

## フロントエンド設計

### 認証

- `@supabase/supabase-js` で Supabase クライアント初期化
- `useAuth` / `useSession` フックでセッション管理・自動リフレッシュ
- `LoginPage` — Google/GitHub ボタンのログインページ
- `AuthGuard` — 未認証時に LoginPage へリダイレクト
- `UserMenu` — ヘッダー右上のユーザーアイコン・ログアウト

### 課金

- `PricingPage` — プラン選択 → Stripe Checkout へ遷移
- `BillingPortal` — プラン変更・解約（Stripe Portal 遷移）
- `PlanBadge` — 現在のプラン表示
- `useSubscription` — サブスク状態の取得

### APIリクエスト

- EE有効時、Axios インターセプターで `Authorization: Bearer <JWT>` を自動付与
- EE無効時はインターセプターがスキップされ、現状と同じ動作

### App.tsx の分岐

```tsx
function App() {
  if (isEnterpriseEnabled()) {
    return (
      <AuthGuard>
        <AppContent />
      </AuthGuard>
    );
  }
  return <AppContent />;
}
```

## データフロー

### 認証フロー

1. ユーザーが LoginPage で「Sign in with Google」をクリック
2. Supabase Auth → Google OAuth 同意画面
3. Google → Supabase コールバック → JWT 発行
4. フロントエンドが JWT を受け取り、セッション保持
5. 以降の API リクエストに `Authorization: Bearer <JWT>` を付与
6. バックエンドが JWT 検証 → user_id 抽出 → 既存ロジックにそのまま渡す

### 課金フロー

1. ユーザーが PricingPage でプランを選択
2. フロントエンド → `POST /ee/billing/create-checkout-session`
3. バックエンド → Stripe Checkout Session 作成 → URL を返す
4. フロントエンド → Stripe Checkout ページにリダイレクト
5. 決済完了 → Stripe → `POST /ee/billing/webhook`
6. バックエンド → SubscriptionModel に DB 保存
7. フロントエンド → サブスク状態を再取得 → UI 更新

## 環境変数

| 変数 | OSS | Enterprise |
|------|-----|-----------|
| `ENTERPRISE_ENABLED` | `false`（デフォルト） | `true` |
| `SUPABASE_URL` | 不要 | 必須 |
| `SUPABASE_ANON_KEY` | 不要 | 必須 |
| `SUPABASE_JWT_SECRET` | 不要 | 必須 |
| `STRIPE_API_KEY` | 不要 | 必須 |
| `STRIPE_WEBHOOK_SECRET` | 不要 | 必須 |
| `VITE_ENTERPRISE_ENABLED` | `false` | `true` |
| `VITE_SUPABASE_URL` | 不要 | 必須 |
| `VITE_SUPABASE_ANON_KEY` | 不要 | 必須 |
| `VITE_STRIPE_PUBLISHABLE_KEY` | 不要 | 必須 |
