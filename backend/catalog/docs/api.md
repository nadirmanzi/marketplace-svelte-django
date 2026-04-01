# Category API Reference

## Public Endpoints (No Authentication Required)

These endpoints return only **active** categories.

### `GET /catalog/categories/`
Returns the full category tree — active root categories with nested children.

**Response** `200 OK`
```json
{
  "status": "success",
  "data": [
    {
      "category_id": "uuid",
      "name": "Electronics",
      "slug": "electronics",
      "description": "...",
      "image": null,
      "is_active": true,
      "children": [
        {
          "category_id": "uuid",
          "name": "Phones",
          "slug": "phones",
          "children": []
        }
      ]
    }
  ]
}
```

---

### `GET /catalog/categories/{slug}/`
Retrieve a single category by its slug, with nested subcategories.

| Parameter | Type   | Description             |
|-----------|--------|-------------------------|
| `slug`    | string | URL-friendly identifier |

**Response** `200 OK` — Category tree object  
**Response** `404 Not Found` — Inactive or non-existent slug

---

## Management Endpoints (Staff Only)

All management endpoints require `Authorization: Bearer <access_token>` and `is_staff=True`.

### `GET /catalog/categories/manage/`
Flat, paginated, filterable list of **all** categories (including inactive).

**Query Filters:**

| Filter            | Type     | Description                      |
|-------------------|----------|----------------------------------|
| `name`            | string   | Case-insensitive partial match   |
| `is_active`       | boolean  | Filter by active status          |
| `parent`          | UUID     | Filter by parent category ID     |
| `is_root`         | boolean  | `true` for top-level categories  |
| `created_at_after`| datetime | Created on or after this date    |
| `created_at_before`| datetime| Created on or before this date   |

**Response** `200 OK` — Paginated list with `metadata` and `items`

---

### `POST /catalog/categories/manage/`
Create a new category.

**Request Body:**
```json
{
  "name": "Fashion",
  "slug": "fashion",
  "description": "Clothing and accessories",
  "parent": "uuid-of-parent-or-null",
  "is_active": true
}
```

| Field         | Required | Default | Description                   |
|---------------|----------|---------|-------------------------------|
| `name`        | ✅       |         | Category display name         |
| `slug`        | ❌       | auto    | URL slug (auto-generated)     |
| `description` | ❌       | `""`    | Category description          |
| `image`       | ❌       | `null`  | Category image (multipart)    |
| `parent`      | ❌       | `null`  | Parent category UUID          |
| `is_active`   | ❌       | `true`  | Visibility toggle             |

**Response** `201 Created` — Full category object

---

### `GET /catalog/categories/manage/{pk}/`
Retrieve a single category by UUID.

**Response** `200 OK`

---

### `PUT /catalog/categories/manage/{pk}/`
Full update of a category. All writable fields required.

**Response** `200 OK`

---

### `PATCH /catalog/categories/manage/{pk}/`
Partial update. Only send the fields you want to change.

**Response** `200 OK`

---

### `POST /catalog/categories/manage/{pk}/deactivate/`
Deactivate a category **and cascade to all descendants**.

> [!WARNING]
> This cascades. All children and grandchildren will also be deactivated.

**Response** `200 OK` — Updated category  
**Response** `409 Conflict` — Already inactive

---

### `POST /catalog/categories/manage/{pk}/activate/`
Re-activate a single category.

> [!NOTE]
> Activation does **not** cascade. Each child must be individually re-activated to prevent accidental mass-visibility changes.

**Response** `200 OK` — Updated category  
**Response** `409 Conflict` — Already active
