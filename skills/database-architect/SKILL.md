---
name: database-architect
description: "Use when designing relational (PostgreSQL/MySQL/SQLite) or NoSQL (MongoDB/Redis) data models, migrations, ORM entities, indexes, and seed fixtures."
---

# Database Architect Superpower

Design normalized, performant, and maintainable schemas with seamless migration paths and seed fixtures.

## Key Checklist

1. **Entity-Relationship Modeling**:
   - Primary keys (`id` UUID or AUTOINCREMENT INTEGER).
   - Foreign keys with `ON DELETE CASCADE` or `ON DELETE SET NULL` constraints.
   - Timestamps: `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, `updated_at TIMESTAMP`.
2. **Indexing Strategy**:
   - Add indexes on foreign keys and frequently queried fields (`email`, `username`, `slug`, `status`).
   - Unique constraints on natural keys.
3. **ORM & Query Builders**:
   - SQLAlchemy / Prisma / TypeORM / Drizzle / Raw SQLite with parameterized queries (prevents SQL injection).
4. **Seed & Migration Scripts**:
   - Include initial schema creation DDL and seed data generation for immediate development/testing.

## Resource Reference

Read `schema-patterns.md` for SQLite and PostgreSQL schema templates:
`ACTION: skill INPUT: {"name": "database-architect", "resource": "schema-patterns.md"}`
