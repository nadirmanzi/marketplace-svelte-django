# Users App API Documentation

This document outlines the API structure, methods, expected bodies, and authentication requirements for the `users` app endpoints.

**Note:** All paths are prefixed with the root configuration router (e.g., `/api/users/`).

---

## 1. Authentication Endpoints

### Login
- **URL**: `/auth/login/`
- **Method**: `POST`
- **Permissions**: Public (`AllowAny`)
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
- **Description**: Returns JWT `access` and `refresh` tokens on successful authentication. Old sessions are invalidated.

### Logout
- **URL**: `/auth/logout/`
- **Method**: `POST`
- **Permissions**: Authenticated (`IsAuthenticated`)
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
  ```json
  {
    "refresh": "eyJ..."
  }
  ```
- **Description**: Blacklists the refresh token and increments `session_version` to invalidate the access token.

### Token Refresh
- **URL**: `/auth/token/refresh/`
- **Method**: `POST`
- **Permissions**: Public (`AllowAny`)
- **Body**:
  ```json
  {
    "refresh": "eyJ..."
  }
  ```
- **Description**: Provides a fresh access token without hitting the DB. Depending on simple JWT settings, generates and rotates the refresh token.

### Token Verify
- **URL**: `/auth/token/verify/`
- **Method**: `POST`
- **Permissions**: Public (`AllowAny`)
- **Body**:
  ```json
  {
    "token": "eyJ..."
  }
  ```
- **Description**: Validates that the provided token hasn't expired or been blacklisted.

---

## 2. User Management Endpoints

All management endpoints are rooted at `/management/`. Access to the various lists and items depends on the `UserActionPermission` policy.

### Register User
- **URL**: `/management/`
- **Method**: `POST`
- **Permissions**: Public (`AllowAny`)
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "full_name": "John Doe",
    "telephone_number": "+1234567890", 
    "password": "secure_password"
  }
  ```
- **Description**: Creates a new user. `telephone_number` is optional but stringently validated via `phonenumbers`. Returns the read-only user payload.

### Current User Profile
- **URL**: `/management/me/`
- **Method**: `GET`
- **Permissions**: Authenticated (`IsAuthenticated`)
- **Headers**: `Authorization: Bearer <access_token>`
- **Description**: Returns the comprehensive read-only profile properties of the currently authenticated user.

### Change Password
- **URL**: `/management/change-password/`
- **Method**: `POST`
- **Permissions**: Authenticated (`IsAuthenticated`)
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
  ```json
  {
    "old_password": "CurrentPassword123",
    "new_password": "NewSecurePassword456!",
    "confirm_password": "NewSecurePassword456!"
  }
  ```
- **Description**: Updates the session version causing universal logouts for old tokens. Returns fresh tokens within the response body.

### List Users
- **URL**: `/management/`
- **Method**: `GET`
- **Permissions**: Authenticated (`IsAuthenticated`)
- **Headers**: `Authorization: Bearer <access_token>`
- **Description**: 
  - Standard users only receive their own array item. 
  - Staff users (`is_staff`, `view_user`) acquire a paginated list of all active users.
  - Superusers view a paginated list of all users, inclusive of soft-deleted ones.

### Retrieve User
- **URL**: `/management/{pk}/`
- **Method**: `GET`
- **Permissions**: Authenticated + Ownership or Staff (`UserActionPermission`)
- **Headers**: `Authorization: Bearer <access_token>`
- **Description**: Fetches individual profile properties.

### Update User
- **URL**: `/management/{pk}/`
- **Method**: `PUT` / `PATCH`
- **Permissions**: Authenticated + Ownership or Staff with `change_user` (`UserActionPermission`)
- **Body**:
  ```json
  {
    "full_name": "Jane Doe",
    "telephone_number": "+0987654321" 
  }
  ```
- **Description**: Partially updates the user's mutable fields. Avoid modifying `email` or `password` directly through this endpoint.

---

## 3. Administrative / Staff Endpoints

### Deactivate User
- **URL**: `/management/{pk}/deactivate/`
- **Method**: `POST`
- **Permissions**: Staff only
- **Description**: Temporarily suspends the account, preventing login constraints.

### Activate User
- **URL**: `/management/{pk}/activate/`
- **Method**: `POST`
- **Permissions**: Staff only
- **Description**: Re-enables a suspended/soft-deleted user account.

### Soft-Delete User
- **URL**: `/management/{pk}/soft-delete/`
- **Method**: `POST`
- **Permissions**: Staff only
- **Description**: Marks the user securely as deleted (timestamps `soft_deleted_at`), disables login validity, whilst preserving rows relation.

---

## 4. Superuser Policy Endpoints

### Set Staff Status
- **URL**: `/management/{pk}/set-staff-status/`
- **Method**: `POST`
- **Permissions**: Superusers only
- **Body**:
  ```json
  {
    "is_staff": true
  }
  ```

### Set Superuser Status
- **URL**: `/management/{pk}/set-superuser-status/`
- **Method**: `POST`
- **Permissions**: Superusers only
- **Body**:
  ```json
  {
    "is_superuser": true
  }
  ```

### Manage Groups
- **URL**: `/management/{pk}/manage-groups/`
- **Method**: `POST`
- **Permissions**: Superusers only
- **Body**:
  ```json
  {
    "action": "add", 
    "group_ids": [1, 2]
  }
  ```
- **Note**: `action` must be either `"add"` or `"remove"`.

### Manage Permissions
- **URL**: `/management/{pk}/manage-permissions/`
- **Method**: `POST`
- **Permissions**: Superusers only
- **Body**:
  ```json
  {
    "action": "remove",
    "permission_ids": [5, 10]
  }
  ```
- **Note**: `action` must be either `"add"` or `"remove"`.
