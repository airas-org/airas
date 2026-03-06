# Mobile Layout Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add responsive mobile layout support so the app is usable on smartphone screens.

**Architecture:** Add a `useIsMobile()` hook using `matchMedia`, then modify App.tsx to: (1) auto-close sidebar on mobile, (2) show sidebar as overlay with backdrop on mobile, (3) auto-close sidebar on nav item click, (4) adjust topbar icons for mobile.

**Tech Stack:** React, Tailwind CSS v4, existing Subframe UI components

---

### Task 1: Create useIsMobile hook

**Files:**
- Create: `frontend/src/hooks/use-mobile.ts`

### Task 2: Mobile sidebar - default closed + overlay with backdrop

**Files:**
- Modify: `frontend/src/App.tsx`

### Task 3: Auto-close sidebar on nav click (mobile)

**Files:**
- Modify: `frontend/src/App.tsx`

### Task 4: Topbar mobile adjustments

**Files:**
- Modify: `frontend/src/App.tsx`
