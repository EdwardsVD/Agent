# Fullstack Best Practices

1. **Separation of Concerns**: Keep API routes, business logic (services), and data access (repositories/models) in distinct modules.
2. **Unified Error Handling**: Return consistent JSON errors:
   `{"error": true, "message": "Item not found", "code": 404}`
3. **Environment Parity**: Always use `.env` or environment variables for ports, secret keys, and database paths.
4. **Mobile & Termux Friendly**: Prefer lightweight SQLite for embedded databases and self-contained static assets (via CDN or bundled local CSS/JS) so the app runs instantly without heavy build steps.
