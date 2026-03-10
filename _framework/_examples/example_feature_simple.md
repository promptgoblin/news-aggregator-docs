# Feature: Dark Mode Toggle

<!-- TOKEN BUDGET: 600 tokens | Use for straightforward features <500 LOC -->
<!-- EXAMPLE: This is a filled example showing how to use template_FEATURE_SIMPLE.md -->

## User Intent

**Goal**: Users want to switch between light and dark color themes to reduce eye strain and match their system preferences or time of day.

**Success Criteria**:
- User can toggle dark/light mode with one click
- System remembers preference across sessions
- Theme applies immediately without page reload
- Respects system theme preference by default

**User Flow**:
1. User clicks theme toggle button in header → 2. System applies dark/light theme instantly → 3. Result: UI updates, preference saved

## Status: Complete
**Last Updated**: 2025-10-05

## Implementation

Simple CSS variable swap with localStorage persistence. On load, check localStorage for saved preference, fallback to system preference via `prefers-color-scheme` media query. Toggle button cycles through light→dark→auto.

**Key Files**:
- `src/components/ThemeToggle.tsx` - Toggle button component
- `src/hooks/useTheme.ts` - Theme state management hook
- `src/styles/themes.css` - CSS variables for light/dark themes

**Data Model**:
```typescript
type Theme = 'light' | 'dark' | 'auto';

// Stored in localStorage
interface ThemePreference {
  theme: Theme;
}
```

## Dependencies

**Requires**:
- None - standalone feature

**Configuration**:
- No environment variables needed
- Themes defined in `src/styles/themes.css`

## Testing
- [x] Works as intended (toggle cycles through modes correctly)
- [x] Edge cases handled (localStorage not available fallback)
- [x] Error states graceful (invalid stored value defaults to 'auto')

## Implementation Notes
- 2025-10-04: Used CSS variables instead of class swapping - cleaner approach
- 2025-10-05: Added 'auto' mode to respect system preference - user request

## Outstanding
- [ ] Add transition animations between theme changes (nice-to-have)
