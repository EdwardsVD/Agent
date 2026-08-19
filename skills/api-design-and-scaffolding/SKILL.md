---
name: api-design-and-scaffolding
description: "Use when designing, generating, or refactoring REST, GraphQL, or gRPC APIs with schemas, validation, rate limiting, error handling, and OpenAPI documentation."
---

# API Design & Scaffolding Superpower

Design and implement production-grade, predictable, and resilient APIs.

## Key Principles

1. **RESTful Resource Naming**:
   - `GET /api/v1/items` -> List items (supports `?page=1&limit=20&search=...`)
   - `POST /api/v1/items` -> Create item (returns 201 Created)
   - `GET /api/v1/items/:id` -> Get single item
   - `PUT/PATCH /api/v1/items/:id` -> Update item
   - `DELETE /api/v1/items/:id` -> Delete item (returns 200 or 204)
2. **Strict Request Validation**:
   - Validate payloads before execution (Pydantic / Joi / custom validator).
   - Return 422/400 with specific field-level error messages.
3. **Status Codes & Headers**:
   - Correct HTTP status codes (200, 201, 204, 400, 401, 403, 404, 422, 500).
   - Standard Content-Type `application/json; charset=utf-8`.
4. **Resilience & Middleware**:
   - Rate limiting, CORS, request ID logging, and global uncaught exception handlers.

## Resource Reference

Read `api-standards.md` for error format conventions:
`ACTION: skill INPUT: {"name": "api-design-and-scaffolding", "resource": "api-standards.md"}`
