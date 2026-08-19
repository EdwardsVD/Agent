---
name: fullstack-code-generator
description: "Use when building complete full-stack web applications (frontend UI, backend API, database, authentication, deployment config) in one coherent structure."
---

# Fullstack Code Generator Superpower

Master end-to-end fullstack development: create clean frontend user interfaces, robust backend REST/GraphQL APIs, persistent data layers, authentication systems, and seamless deployment setups.

## Execution Blueprint

1. **Stack Selection**:
   - Backend: Python (FastAPI/Flask) or Node.js (Express)
   - Frontend: Modern Single-Page App (HTML5 + Tailwind CSS + Vanilla JS/React/Vue)
   - Database: SQLite (zero-config, works everywhere including Termux) or PostgreSQL
2. **API Contract**: Define request/response JSON schemas before writing endpoints.
3. **Frontend Integration**:
   - Deliver clean responsive UI with dark/light mode.
   - Connect frontend fetch calls directly to backend endpoints with proper error handling and loading indicators.
4. **Security & State**:
   - Password hashing with bcrypt / hashlib + salt.
   - JWT or session tokens for authenticated routes.
   - CORS middleware enabled for local development.
5. **Verification**:
   - Test backend routes with automated unit/integration tests.
   - Verify static asset serving and client-server communication.

## Resource Reference

Read `fullstack-best-practices.md` for architecture guidelines:
`ACTION: skill INPUT: {"name": "fullstack-code-generator", "resource": "fullstack-best-practices.md"}`
