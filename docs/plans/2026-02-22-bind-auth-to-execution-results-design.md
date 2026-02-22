# Design: Bind Authenticated User to Execution Results

## Problem

Authentication infrastructure exists (JWT middleware, Supabase, AuthGuard) but execution results are saved with a hardcoded `SYSTEM_USER_ID` instead of the actual authenticated user.

## Approach

Use the existing `get_current_user_id()` FastAPI dependency (which returns JWT user when EE enabled, `SYSTEM_USER_ID` when disabled) to inject `created_by` server-side in all endpoints that create records.

## Changes

### 1. Autonomous Research (`topic_open_ended_research`)

- **Route**: Add `Depends(get_current_user_id)` to the `/run` endpoint
- **Subgraph**: Accept `created_by` parameter instead of hardcoding UUID
- Remove hardcoded UUID from `_create_record()` in subgraph

### 2. Assisted Research Session Creation

- **Route**: Add `Depends(get_current_user_id)` to `POST /session`
- **Schema**: Remove `created_by` from `AssistedResearchSessionCreateRequest`
- Use server-side user ID instead of client-provided value

### 3. Assisted Research Step Creation

- **Route**: Add `Depends(get_current_user_id)` to `POST /step`
- **Schema**: Remove `created_by` from `AssistedResearchStepCreateRequest`
- Use server-side user ID instead of client-provided value

## Principles

- `created_by` is determined server-side only (never trust client)
- EE disabled: falls back to `SYSTEM_USER_ID` (no breaking changes)
- No frontend changes needed (axios interceptor already sends JWT)
