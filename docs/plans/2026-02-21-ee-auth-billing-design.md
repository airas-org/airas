# Enterprise Edition: Auth Design

## Overview

AIRAS にエンタープライズ向けの認証（Supabase Auth）を追加する。authentication only (no billing for now)。
OSS版は現状の動作を維持し、`ee/` ディレクトリに ELv2 ライセンスで分離する。

## 決定事項

- **認証**: Supabase Auth（ソーシャルログインのみ: Google + GitHub）
- **アクセス制御**: EE有効時は全機能ログイン必須
- **ライセンス**: `ee/` ディレクトリに Elastic License v2 (ELv2)
- **アプローチ**: フロントエンドで Supabase SDK 直接統合、バックエンドで JWT 検証

## ディレクトリ構成

```
frontend/src/
├── ee/
│   ├── LICENSE                  # Elastic License v2
│   ├── config.ts                # isEnterpriseEnabled()
│   └── auth/
│       ├── components/
│       │   ├── LoginPage.tsx
│       │   ├── AuthGuard.tsx
│       │   ├── AuthCallback.tsx
│       │   └── UserMenu.tsx
│       ├── hooks/
│       │   ├── useAuth.ts
│       │   └── useSession.ts
│       └── lib/
│           └── supabase.ts

backend/api/
├── ee/
│   ├── LICENSE                  # Elastic License v2
│   ├── auth/
│   │   ├── middleware.py        # JWT検証ミドルウェア
│   │   ├── dependencies.py     # get_current_user (FastAPI Depends)
│   │   └── routes.py           # /ee/auth/* エンドポイント
│   └── settings.py             # EE設定
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

## バックエンド設計

### 認証

- `get_current_user_id()` の分岐: EE有効時は JWT 検証、無効時は `SYSTEM_USER_ID`
- Supabase JWT の署名検証・有効期限チェック（`PyJWT` 使用）
- 認証の実体は Supabase 側。バックエンドは JWT 検証のみ

### 追加パッケージ

- `PyJWT` — JWT検証

## フロントエンド設計

### 認証

- `@supabase/supabase-js` で Supabase クライアント初期化
- `useAuth` / `useSession` フックでセッション管理・自動リフレッシュ
- `LoginPage` — Google/GitHub ボタンのログインページ
- `AuthGuard` — 未認証時に LoginPage へリダイレクト
- `UserMenu` — ヘッダー右上のユーザーアイコン・ログアウト

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

## 環境変数

| 変数 | OSS | Enterprise |
|------|-----|-----------|
| `ENTERPRISE_ENABLED` | `false`（デフォルト） | `true` |
| `SUPABASE_URL` | 不要 | 必須 |
| `SUPABASE_ANON_KEY` | 不要 | 必須 |
| `SUPABASE_JWT_SECRET` | 不要 | 必須 |
| `VITE_ENTERPRISE_ENABLED` | `false` | `true` |
| `VITE_SUPABASE_URL` | 不要 | 必須 |
| `VITE_SUPABASE_ANON_KEY` | 不要 | 必須 |
