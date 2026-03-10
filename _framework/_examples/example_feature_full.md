# Feature: User Authentication

<!-- TOKEN BUDGET: 1,000 tokens | If >1,200 & logically divisible, split to sub-features -->
<!-- EXAMPLE: This is a filled example showing how to use template_FEATURE.md -->

## User Intent

### Goal
Users need to securely create accounts, log in, and maintain authenticated sessions across the application. Without authentication, we cannot personalize experiences, protect user data, or enable user-specific features.

### Success Criteria
- User can register with email/password in <30 seconds
- User can log in and stay authenticated for 7 days (configurable)
- System enforces secure password requirements (min 12 chars, complexity)
- Experience feels seamless - no unnecessary re-authentication
- Failed login attempts are rate-limited to prevent brute force

### User Flow
1. User clicks "Sign Up" and enters email/password
2. System validates input, creates account, sends verification email
3. User clicks verification link in email
4. User is redirected to app, automatically logged in
5. Result: User has account and is authenticated

## Status: Complete
**Started**: 2025-09-15
**Last Updated**: 2025-10-01

## References
- Plan: [plan/PLAN.md#features]
- Design: [plan/plan_section_auth.md]
- Related: [feature_user_profile.md] (requires auth)
- API: [reference/lib_bcrypt.md], [reference/lib_jwt.md]

## Implementation

### Approach
JWT-based authentication with HTTP-only cookies. Passwords hashed with bcrypt (12 rounds). Tokens expire after 7 days but include refresh mechanism. Email verification required before account is fully active.

### Key Components
- **AuthService**: Registration, login, logout, token refresh
- **AuthMiddleware**: Validates JWT on protected routes
- **EmailVerification**: Sends verification emails, validates tokens
- **PasswordReset**: Secure password reset flow via email

### Key Files
- `src/services/auth.ts` - Core authentication logic
- `src/api/auth.ts` - Auth endpoints (register, login, logout, refresh)
- `src/middleware/authenticate.ts` - JWT validation middleware
- `src/utils/email.ts` - Email sending utility
- `tests/auth.test.ts` - Auth flow tests

### Data Model
```typescript
interface User {
  id: string;
  email: string;
  passwordHash: string;
  emailVerified: boolean;
  verificationToken?: string;
  resetToken?: string;
  resetTokenExpiry?: Date;
  createdAt: Date;
  lastLogin?: Date;
}

interface AuthTokens {
  accessToken: string;  // 15min expiry
  refreshToken: string; // 7 day expiry
}
```

## Dependencies

### Setup Required
- [setup/setup_database.md]: PostgreSQL with users table
- [setup/setup_email.md]: SMTP configuration for verification emails

### Features Required
- None - this is a foundational feature

### Requires This Feature
- [feature_user_profile.md]: Needs authenticated user context
- [feature_settings.md]: User must be authenticated
- [feature_payments.md]: Payment actions require auth

### External Services
- **bcrypt**: Password hashing - See [reference/lib_bcrypt.md]
- **jsonwebtoken**: JWT creation/validation - See [reference/lib_jwt.md]
- **nodemailer**: Email sending - See [reference/lib_nodemailer.md]

## Configuration
- `JWT_SECRET`: Secret key for signing tokens - Must be strong, rotated regularly
- `JWT_ACCESS_EXPIRY`: Access token lifetime (default: 15m)
- `JWT_REFRESH_EXPIRY`: Refresh token lifetime (default: 7d)
- `BCRYPT_ROUNDS`: Hashing rounds (default: 12)
- `EMAIL_VERIFICATION_REQUIRED`: Enforce email verification (default: true)

## Edge Cases & Considerations

### Handled
- **Duplicate email registration**: Returns "Email already exists" error
- **Concurrent login sessions**: Multiple devices supported, each gets own refresh token
- **Token expiry during request**: Middleware returns 401, client auto-refreshes
- **Password reset race condition**: Reset tokens invalidated on use or new request

### Limitations
- **No 2FA yet**: Planned for v2, tracked in [feature_2fa.md]
- **No social auth**: OAuth integration deferred to post-MVP
- **Session length fixed**: Per-user session customization not supported

### Performance
- **Password hashing**: bcrypt rounds = 12 (balanced security vs. speed, ~200ms)
- **Token validation**: Cached public key, <1ms validation
- **Database queries**: Indexed on email, <10ms lookup

### Security
- **Passwords**: Hashed with bcrypt, never stored or logged in plaintext
- **Tokens**: HTTP-only cookies prevent XSS, secure flag in production
- **Rate limiting**: 5 failed attempts → 15min lockout per IP
- **Email verification**: Required before account is fully active
- **CSRF protection**: SameSite=Strict cookies + CSRF tokens on state-changing ops

## Testing
- [x] Unit tests: AuthService methods (register, login, token generation)
- [x] Integration: Full registration → verification → login flow
- [x] Manual: happy path (register, verify, login, access protected route)
- [x] Manual: error states (invalid credentials, expired token, unverified email)
- [x] Edge case: duplicate registration
- [x] Edge case: concurrent sessions on multiple devices
- [x] Performance: Login completes in <300ms (p95)
- [x] Security: Penetration test of auth flows (no vulnerabilities found)

## Implementation Notes
- 2025-09-20: Changed from session-based to JWT - better for API clients
- 2025-09-25: Added refresh token rotation - prevents token theft replay attacks
- 2025-09-28: Increased bcrypt rounds from 10→12 - OWASP recommendation
- 2025-10-01: Added rate limiting after observing brute force attempts in logs

## Outstanding
- [ ] Add password strength meter to UI (UX improvement)
- [ ] Implement "remember this device" feature for trusted devices
- [ ] Add admin endpoint to force-expire all user sessions
