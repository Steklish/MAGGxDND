# Issue: Redirect to Home Page After Character Creation

## Status
✅ **COMPLETED** - Merged into UIv0.3 branch

## Description
After successfully creating a character, users are now redirected to the home page instead of the profile page, allowing them to immediately see their new character in the characters tab.

## Problem
Previously, `handleCharacterComplete` navigated to `'profile'` page, which was not the expected behavior. Users expected to return to the home page after creating a character.

## Solution
Changed `setCurrentPage('profile')` to `setCurrentPage('home')` in the `handleCharacterComplete` function in `App.tsx`.

## Files Modified
- `frontend/src/App.tsx` - Updated `handleCharacterComplete` redirect target

## Commit
**Hash:** `2ebf358`
**Message:** fix: redirect to home page after character creation instead of profile
