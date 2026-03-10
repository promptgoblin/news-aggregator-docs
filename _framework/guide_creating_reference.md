# Guide: Creating Reference Documents

**Use when**: Documenting external APIs, libraries, or services

## When to Create

**Create `reference/*.md` when**:
- API used in 2+ features
- >5 endpoints OR complex authentication flow
- Config requires >3 environment variables

**Just link inline when**:
- <3 methods used
- One-time reference
- Official docs are clear

## Creating Reference Doc

1. Copy appropriate template or create from scratch
2. Name: `api_[service]_[topic].md` or `lib_[library]_[topic].md`
3. Focus on how YOU use it, not full API docs
4. Include auth, common gotchas, rate limits
5. Add to `reference/_index.md`

## What to Document

**Essential**:
- Authentication setup
- Endpoints/methods you actually use
- Common gotchas and errors
- Rate limits / quotas
- Configuration (env vars)

**Skip**:
- Full API reference (link to official docs)
- Methods you don't use
- Theoretical capabilities

## Document Types

**API Reference** (`api_[service]_[topic].md`):
- External REST/GraphQL APIs
- Focus on endpoints used
- Example: `api_stripe_webhooks.md`

**Library Reference** (`lib_[library]_[topic].md`):
- NPM packages, gems, etc.
- Configuration and common patterns
- Example: `lib_prisma_relations.md`

## Template Structure

Since reference docs vary widely, no strict template. Include:

```markdown
# API: [Service] - [Topic]

## Authentication
[How to auth - API keys, OAuth, etc.]

## Configuration
- `ENV_VAR`: [Purpose]

## Endpoints We Use

### [Endpoint Name]
**URL**: `POST /api/endpoint`
**Purpose**: [Why we use it]
**Request**:
```json
{example}
```
**Response**:
```json
{example}
```

## Common Gotchas
- [Issue]: [Solution]

## Rate Limits
[Limits and how to handle]

## Official Docs
[Link to official documentation]
```

## After Creating

1. Add to `reference/_index.md`
2. Link from features that use it
3. Update `PLAN.md` if foundational
4. Verify naming follows conventions

## Naming Pattern

- `api_[service]_[topic].md`
- `lib_[library]_[topic].md`
- `spec_[standard].md`
- `guide_[topic].md` (third-party guides)

Always lowercase, use underscores.

## Keep It Focused

Reference docs should be:
- ✅ How WE use the API/library
- ✅ Common gotchas WE encountered
- ✅ Examples from OUR codebase
- ❌ NOT comprehensive API documentation
- ❌ NOT copy-paste from official docs
