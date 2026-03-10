# Plan Section: Authentication Strategy

<!-- TOKEN BUDGET: 1,200 tokens | If >1,500, topic too broad - split sections -->
<!-- EXAMPLE: This is a filled example showing how to use template_PLAN_SECTION.md -->

**Last Updated**: 2025-09-15

## Overview

Authentication approach for user identity management across web app, mobile app, and API clients. Primary goals: security, developer experience, multi-device support.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Auth method | JWT (not sessions) | Better for API clients, mobile apps |
| Token storage | HTTP-only cookies (web), secure storage (mobile) | Prevents XSS attacks |
| Password hashing | bcrypt (12 rounds) | Industry standard, OWASP recommended |
| Token expiry | 15min access, 7d refresh | Balance security vs. UX |
| Email verification | Required | Prevent fake accounts, confirm contact method |

## Design

### Architecture
```
Client → API (JWT middleware) → Protected routes
         ↓
      Auth Service (bcrypt, JWT generation)
         ↓
      User DB (hashed passwords only)
```

### Token Flow
1. User logs in with email/password
2. Server validates credentials, generates access token (15min) + refresh token (7d)
3. Tokens returned in HTTP-only cookies
4. Client includes cookies on all requests
5. Middleware validates access token
6. On expiry, client hits /refresh endpoint with refresh token
7. Server issues new access token

### Security Measures
- Passwords hashed with bcrypt (12 rounds, never stored plaintext)
- Tokens in HTTP-only, SameSite=Strict cookies
- Rate limiting: 5 failed attempts → 15min IP lockout
- Email verification required before account activation
- CSRF protection via tokens on state-changing operations

## Alternatives Considered

### Session-based auth (rejected)
**Pros**: Simpler server-side invalidation, familiar pattern
**Cons**: Harder to scale horizontally, poor fit for mobile/API clients
**Decision**: JWT better for our multi-client architecture

### OAuth-only (deferred)
**Pros**: No password management, leverages trusted providers
**Cons**: Vendor lock-in, requires internet connection, complex setup
**Decision**: Implement email/password first, add OAuth post-MVP

### Magic links instead of passwords (rejected)
**Pros**: No password to remember, simpler UX
**Cons**: Email dependency, slower login flow, user confusion
**Decision**: Keep traditional auth, may add as alternative in v2

## Implementation Notes

**Dependencies**:
- bcrypt library for password hashing
- jsonwebtoken library for JWT ops
- Database table for users (email, passwordHash, verificationToken, etc.)

**Configuration Required**:
- JWT_SECRET environment variable (strong random string, rotated quarterly)
- SMTP credentials for verification emails
- Token expiry durations (configurable via env vars)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| JWT secret leaked | High - all tokens compromised | Store in secrets manager, rotate regularly, monitor for unusual activity |
| Brute force attacks | Medium - account takeover | Rate limiting, account lockout after N attempts, CAPTCHA on repeated failures |
| Token theft (XSS) | High - session hijacking | HTTP-only cookies, CSP headers, input sanitization |
| Database breach | Critical - password exposure | bcrypt hashing, salt per password, encryption at rest |

## Performance Considerations

- Password hashing adds ~200ms per login (acceptable for security benefit)
- Token validation <1ms with proper JWT library
- Database indexed on email field for fast user lookups
- Consider Redis caching for frequently accessed user data (post-MVP)

## Plan Section Dependencies

**Depends On**:
- [plan_section_database.md]: Needs users table schema
- [plan_section_email.md]: Email service for verification

**Required By**:
- [plan_section_api_design.md]: Auth middleware affects all endpoints
- [plan_section_frontend_architecture.md]: Auth state management in UI

## Impact on Features

**Directly Enables**:
- [feature_user_authentication.md]: Implements this plan
- [feature_user_profile.md]: Requires authenticated user context
- [feature_settings.md]: User-specific settings need auth

**Constraints**:
- All protected features must check auth middleware
- Mobile app must handle token refresh gracefully
- Logout must invalidate tokens (track in DB or use short expiry)

## Decision History

**2025-09-10**: Initial decision for JWT-based auth
**2025-09-12**: → Increased bcrypt rounds from 10 to 12 (OWASP update)
**2025-09-15**: → Added refresh token rotation for better security

## Open Questions

- [ ] How to handle password reset flow? (Answer: Email-based reset token, 1hr expiry)
- [x] Support multiple concurrent sessions? (Answer: Yes, each device gets own refresh token)
- [x] 2FA support in v1? (Answer: No, defer to v2 - see [feature_2fa.md])

## Testing Strategy

- Unit tests for password hashing, token generation/validation
- Integration tests for full login/logout flows
- Security tests for common attacks (injection, brute force, XSS)
- Load tests for auth endpoints (target: p95 <300ms)
