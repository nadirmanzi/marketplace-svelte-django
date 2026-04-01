# User Lifecycle & Management

This document outlines the state management, business logic, and permission models governing the lifecycle of a User account in the system.

## 1. Service-Oriented Architecture

To ensure data integrity and reusability, all user state transitions are encapsulated in the `UserManagementService` (`users/services/management_services.py`).

**Views and Admin actions must never modify User status fields directly.**

### Key Service Methods

- `soft_delete_user(user)`: Transitions a user to the "soft-deleted" state.
- `activate_user(user)`: Restores a deactivated or soft-deleted account.
- `set_superuser_status(user, status)`: Includes a safety guard to prevent system lockout (prevents deleting the last superuser).

## 2. Account States

An account exists in one of three primary functional states:

| State            | `is_active` | `is_soft_deleted` | Impact                                                     |
| :--------------- | :---------- | :---------------- | :--------------------------------------------------------- |
| **Active**       | `True`      | `False`           | Full access to the platform.                               |
| **Deactivated**  | `False`     | `False`           | Login blocked. Data visible in admin. Reversible.          |
| **Soft-Deleted** | `False`     | `True`            | Login blocked. Excluded from standard queries. Reversible. |

## 3. Soft-Delete Implementation

We use a "safe" deletion pattern that preserves data for audit and relational integrity.

### Model Mechanics (`users/models.py`)

- **Field**: `is_soft_deleted` and `soft_deleted_at`.
- **Save Hook**: The `User.save()` method enforces state invariants. If `is_soft_deleted` is True, `is_active` is automatically forced to False.
- **Constraints**: A `UniqueConstraint` in the `Meta` class ensures that phone numbers are only unique among **active** (non-deleted) users, allowing a new user to register with a phone number previously used by a deleted account.

### Manager Logic (`users/managers.py`)

The default manager `User.objects` filters out soft-deleted users. To include them (e.g., for reactivation), engineers must use the `all_objects()` manager.

```python
# Standard query (excludes deleted)
active_users = User.objects.all()

# Admin/Recovery query (includes all)
all_users = User.objects.all_objects()
```

## 4. Field-Level Permissions

We use a custom permission class, `UserActionPermission`, to enforce granular control over who can modify what.

### The Role Matrix

- **Superusers**: Absolute access.
- **Staff**: Can view and manage users based on specific Django permissions (`view_user`, `can_soft_delete_user`).
- **Owner (Self)**: Can modify a restricted whitelist of fields: `email`, `full_name`, `telephone_number`.

### Restricted Fields (`SENSITIVE_FIELDS`)

The following fields are protected. Owners **cannot** modify these even on their own profile:

- `is_active`, `is_staff`, `is_superuser`.
- `groups`, `user_permissions`.
- `session_version`, `password_changed_at`.

## 5. Administrative Integrity

The system implements a "Last Superuser Guard" at the service level (`set_superuser_status`). This prevents an admin from accidentally revoking their own (or another's) superuser status if they are the only remaining administrative account, preventing a total system lockout.
