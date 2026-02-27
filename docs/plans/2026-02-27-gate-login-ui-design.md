# Gate-type Login UI Improvement Design

## Date: 2026-02-27

## Overview

Improve the login page UI to a polished full-screen gate-type design while keeping the existing Supabase + Google OAuth authentication mechanism intact.

## Current State

- `LoginPage.tsx`: Simple centered card with plain background, AIRAS logo, and "Sign in with Google" button
- `AuthGuard.tsx`: Already implements gate-type blocking (shows LoginPage when no session)
- EE flag controls whether auth is enabled

## Changes

### LoginPage.tsx UI Improvements

1. **Background**: Add gradient background using brand colors
2. **Card**: Enhanced shadow, increased padding, refined borders
3. **Logo**: Larger display
4. **Subtitle**: Add "AI-powered Research Assistant" tagline
5. **Google Sign-in Button**: Add Google icon, improve styling
6. **Loading State**: Show spinner during sign-in process

### Files Changed

- `frontend/src/ee/auth/components/LoginPage.tsx` (UI only)

### Files NOT Changed

- Authentication logic (`useAuth`, `useSession`, `AuthGuard`)
- Backend auth middleware
- EE flag mechanism
- Axios interceptor

## Design

Center card layout with gradient background. English text maintained.
