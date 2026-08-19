# API Standards and Schemas

## Standard Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {"field": "email", "issue": "Invalid email address format"}
    ]
  },
  "timestamp": "2026-08-19T10:00:00Z"
}
```

## Standard Success Response Structure
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100
  }
}
```
