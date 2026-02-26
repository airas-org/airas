# GitHub OAuth Integration Design

## Overview

Replace the current manual PAT (Personal Access Token) input with a standard GitHub OAuth 2.0 Authorization Code Flow. Users click "Connect with GitHub", authorize on GitHub's page, and return to the app with the connection complete.

## Architecture

### Flow

```
1. User clicks "Connect with GitHub" on Settings page
2. Frontend calls GET /airas/v1/settings/github/oauth/authorize
3. Backend generates a random `state`, stores it in DB (GitHubOAuthStateModel), returns the GitHub authorization URL
4. Frontend redirects to GitHub's authorization page
5. User clicks "Authorize" on GitHub
6. GitHub redirects to GET /airas/v1/settings/github/oauth/callback?code=xxx&state=yyy
7. Backend verifies state, exchanges code for access token via GitHub API
8. Backend saves token + username to GitHubSettingsModel (existing table)
9. Backend redirects browser to frontend URL with ?github=connected query param
10. Frontend detects query param, shows success, reloads settings
```

### Scope

- OAuth scope: `repo,workflow`
- Remove manual PAT input from UI (OAuth only)

## Backend Changes

### New Environment Variables

- `GITHUB_OAUTH_CLIENT_ID` - OAuth App Client ID
- `GITHUB_OAUTH_CLIENT_SECRET` - OAuth App Client Secret
- `FRONTEND_URL` - Frontend URL for redirect after callback (e.g., `http://localhost:5173`)

### New Model: `GitHubOAuthStateModel`

Temporary storage for OAuth state parameter (CSRF protection).

```python
class GitHubOAuthStateModel(SQLModel, table=True):
    __tablename__ = "github_oauth_states"
    id: UUID (PK)
    user_id: UUID (indexed)
    state: str (unique, indexed)
    created_at: datetime
```

### New Endpoints (in `settings.py`)

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | `/settings/github/oauth/authorize` | Yes | Generate state, return GitHub auth URL |
| GET | `/settings/github/oauth/callback` | No* | Exchange code for token, save, redirect to frontend |

*Callback is called by GitHub redirect, so it can't carry the user's auth token. The state parameter maps back to the user_id.

### Modified Files

- `backend/api/routes/v1/settings.py` - Add 2 new endpoints, remove `save_github_settings` (POST /github)
- `backend/api/schemas/settings.py` - Add `GitHubOAuthAuthorizeResponse`, remove `SaveGitHubTokenRequest`
- `backend/src/airas/infra/db/models/github_oauth_state.py` - New model
- `backend/src/airas/usecases/settings/github_settings_service.py` - Add OAuth state management methods
- `backend/src/airas/repository/github_oauth_state_repository.py` - New repository
- `backend/src/airas/container.py` - Register new repository
- `backend/api/main.py` - Callback endpoint needs to be excluded from auth middleware
- `backend/.env.example` - Add new env vars

## Frontend Changes

### `frontend/src/components/pages/settings.tsx`

- Remove token input form
- Add "Connect with GitHub" button (with GitHub icon)
- On click: call `/settings/github/oauth/authorize`, redirect to returned URL
- On page load: check for `?github=connected` query param to show success message
- Keep: connection status display, check connection, remove connection buttons

### `frontend/src/App.tsx`

- Handle `?github=connected` query param (clean URL after detection)

## Security

- `state` parameter prevents CSRF attacks
- Client Secret stays server-side only
- OAuth states expire (cleanup old states on each authorize call)
- Callback endpoint validates state before any token exchange
