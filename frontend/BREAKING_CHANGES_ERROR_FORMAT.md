# ⚠️ BREAKING CHANGE: Unified API Error Response Format

**Date**: 2026-04-17  
**Scope**: ALL backend API error responses (4xx and 5xx)

---

## What Changed

The backend now returns **every** error in a single, unified JSON schema. Previously, the shape varied depending on error type:

### Old (BEFORE) — Inconsistent formats

```json
// Generic errors (401, 403, 404, service errors)
{ "detail": "Human readable message" }

// Validation errors (400)
{ "errors": { "email": ["..."], "non_field_errors": ["..."] } }
```

### New (AFTER) — Single unified format

```json
{
  "success": false,
  "code": "validation_error",
  "detail": "Human-readable summary of the error.",
  "errors": {}
}
```

**Every error response now contains all four fields.** Always.

---

## Field Descriptions

| Field     | Type     | Description                                                                                                |
| :-------- | :------- | :--------------------------------------------------------------------------------------------------------- |
| `success` | `false`  | Always `false` for errors. Can be used as a quick check.                                                   |
| `code`    | `string` | Machine-readable error code. See table below.                                                              |
| `detail`  | `string` | Human-readable summary. For validation errors with only non-field errors, the message is placed here.      |
| `errors`  | `object` | Field-level validation errors as `{ "field_name": ["msg1", "msg2"] }`. Empty `{}` for non-validation errors. |

---

## Error Codes

| `code`                  | HTTP Status | When                                       |
| :---------------------- | :---------- | :----------------------------------------- |
| `validation_error`      | 400         | Serializer / form validation failures       |
| `authentication_failed` | 401         | Missing / invalid / expired credentials     |
| `token_error`           | 401         | JWT token issues (expired, blacklisted)      |
| `permission_denied`     | 403         | Insufficient permissions                     |
| `not_found`             | 404         | Resource not found                           |
| `conflict`              | 409         | State conflict (e.g., already deactivated)   |
| `throttled`             | 429         | Rate limit exceeded                          |
| `server_error`          | 500         | Unhandled server exception                   |

---

## Examples

### 1. Authentication Error (401)
```json
{
  "success": false,
  "code": "authentication_failed",
  "detail": "Given token not valid for any token type.",
  "errors": {}
}
```

### 2. Field Validation Error (400)
```json
{
  "success": false,
  "code": "validation_error",
  "detail": "Validation failed.",
  "errors": {
    "email": ["Enter a valid email address."],
    "password": ["This password is too common."]
  }
}
```

### 3. Cross-Field / Non-Field Validation Error (400)
Non-field errors (e.g., `raise ValidationError("Passwords must match")`) are **consolidated into `detail`**, NOT placed in `errors`.
```json
{
  "success": false,
  "code": "validation_error",
  "detail": "Passwords must match.",
  "errors": {}
}
```

### 4. Permission Denied (403)
```json
{
  "success": false,
  "code": "permission_denied",
  "detail": "You do not have permission to perform this action.",
  "errors": {}
}
```

### 5. Not Found (404)
```json
{
  "success": false,
  "code": "not_found",
  "detail": "Product not found.",
  "errors": {}
}
```

### 6. Rate Limited (429)
```json
{
  "success": false,
  "code": "throttled",
  "detail": "Request was throttled. Expected available in 30 seconds.",
  "errors": {}
}
```

---

## Migration Guide for Frontend

### Old pattern (REMOVE)
```typescript
// ❌ Don't do this anymore
if (response.data.detail) {
  showError(response.data.detail);
} else if (response.data.errors) {
  setFieldErrors(response.data.errors);
}
```

### New pattern (USE THIS)
```typescript
// ✅ Unified parsing
const { success, code, detail, errors } = response.data;

// `detail` always has a human-readable message
showToast(detail);

// `errors` has field-level issues (empty {} if none)
if (Object.keys(errors).length > 0) {
  setFieldErrors(errors);
}

// `code` can be used for programmatic branching
if (code === 'authentication_failed') {
  redirectToLogin();
}
```

---

## Files Affected

- `backend/config/exceptions.py` — Rewritten with unified `_build_error_response`
- `backend/users/serializers.py` — Fixed `RegisterSerializer.create()` to raise plain string `ValidationError`
- `backend/users/tests/test_auth_and_management.py` — Updated assertion to match new schema
