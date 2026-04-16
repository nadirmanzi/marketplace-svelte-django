# Catalog API Guide (Frontend & AI)

This document provides a comprehensive overview of the Catalog API, acting as the ultimate development guide for the Marketplace platform's product management. It thoroughly covers the unified catalog logic, pricing inheritance, discount precedence, url structure, request/response models, and specialized business rules.

---

## 1. Unified Catalog Architecture

The foundation of the catalog relies on inheritance and a strict hierarchy:

### 1.1 Core Entities & Inheritance

- **Categories**: The structural tree. Define constraints and attributes. Categories can optionally have active percentage discounts applied to them, cascading to all products and variants underneath.
- **Attributes**: The schema-less property system. Defined globally or per-category. Products and Variants map values to these constraints.
- **Products (Blueprints)**: The parent representation of an item. Defines the `base_price` (if variants don't override it), global attributes, generic images, and structural `category`.
- **Variants (SKUs)**: The purchasable items. They inherit `base_price`, `images`, and `discount` from the parent product if not explicitly overridden. They hold physical concerns: `stock_quantity`, `sku`, and variant-specific attributes (e.g., color, size).

### 1.2 Unified Pricing Logic & FinalPricingService

The API completely shields the frontend from calculating effective prices. Every category, product, and variant API response returns fully computed pricing fields.

- `base_price`: The pre-discount price. Variants inherit from their Product if not set.
- `final_price`: The discounted price. Guaranteed to be non-negative.
- `discount`: A detailed object explaining _which_ discount was applied, if any.

**Discount Precedence (Guard Method Pattern)**:
A single entity can only output one active discount. The `FinalPricingService` resolves conflicts top-down:

1.  **Variant Level**: Most specific. If the variant has an active discount, it wins.
2.  **Product Level**: Fallback 1. If no variant discount exists, check the parent product.
3.  **Category Level**: Fallback 2. If neither variant nor product has a discount, apply the category's active discount (or its ancestors, depending on implementation).

**Discount Validation Rules**:

- Fixed-amount discounts cannot exceed the `base_price` (computed price won't go below 0).
- Category-wide discounts **must** be percentage-based. Fixed amount category discounts are invalid.
- Percentage discounts cannot exceed 100%.
- Dates: `end_date` must naturally occur after `start_date` if provided.

---

## 2. API URL Structure Overview

All requests are prefixed with `/catalog/`.

**Public APIs (Read Only, AllowAny)**

- `GET /categories/` : Flat list
- `GET /categories/tree/` : Nested tree
- `GET /categories/<uuid>/attributes/` : Attributes for a category
- `GET /products/` : Published products with active variants
- `GET /products/<slug>/` : Single product detail

**Management APIs (Staff & Owners)**

- `CRUD /categories/manage/` : Category management
- `CRUD /products/manage/` : Product blueprint management
- `CRUD /variants/manage/` : Variant SKU management
- `CRUD /attributes/manage/` : Attribute definitions
- `CRUD /discounts/manage/` : Discount definitions

---

## 3. Comprehensive API Reference

### 3.1. Public APIs

#### 3.1.1. List Categories (Flat)

Retrieves a flat list of active categories.

- **URL**: `GET /catalog/categories/`
- **Query Params**: `name` (filter), `is_root` (boolean)
- **Response (200)**:

```json
[
  {
    "category_id": "uuid",
    "name": "Electronics",
    "slug": "electronics",
    "description": "...",
    "image": "url/null",
    "parent_id": "uuid/null",
    "is_active": true,
    "is_root": true,
    "depth": 0,
    "subcategory_count": 5,
    "discount": {
      "discount_id": "uuid",
      "name": "Summer Sale",
      "type": "percentage",
      "value": "15.00",
      "scope": "category"
    } // Or null
  }
]
```

#### 3.1.2. Category Tree

- **URL**: `GET /catalog/categories/tree/`
- **Response (200)**: Returns categories nested recursively under the `children` key. Same schema as flat list, but includes nested structures.

#### 3.1.3. List Public Products

Retrieves published products with their active variations and resolved prices.

- **URL**: `GET /catalog/products/`
- **Query Params**: `category` (UUID), `min_price` (Decimal), `max_price` (Decimal), `name` (String, icontains)
- **Response (200)**: Array of Product Details.

#### 3.1.4. Product Detail (Public)

- **URL**: `GET /catalog/products/{slug}/`
- **Response (200)**:

```json
{
  "product_id": "uuid",
  "name": "Smartphone X",
  "slug": "smartphone-x",
  "description": "...",
  "base_price": "999.00",
  "final_price": "899.10",
  "status": "published",
  "is_published": true,
  "category_id": "uuid",
  "category_name": "Electronics",
  "user_email": "owner@example.com",
  "active_variant_count": 2,
  "discount": {
    "discount_id": "uuid",
    "name": "Fall Sale",
    "type": "percentage",
    "value": "10.00",
    "scope": "product"
  },
  "images": [
    {
      "image_id": 1,
      "image": "url",
      "thumbnail": "url",
      "alt_text": "...",
      "is_feature": true
    }
  ],
  "attributes": [
     {
        "attribute_id": "uuid",
        "name": "Brand",
        "slug": "brand",
        "input_type": "text",
        "value": "TechCo"
     }
  ],
  "variants": [
    {
      "variant_id": "uuid",
      "sku": "SM-X-128-BLK",
      "name": "128GB Black",
      "base_price": "999.00",
      "final_price": "899.10",
      "stock_quantity": 50,
      "in_stock": true,
      "is_active": true,
      "images": [], // falls back to product images if empty
      "attributes": [],
      "discount": {...}
    }
  ]
}
```

---

### 3.2. Management APIs

_Note: Requires Authentication. Users see their own items. Staff/Admins see all items._

#### 3.2.1. Products Management

- **List / Create**: `GET|POST /catalog/products/manage/`
- **Detail / Update**: `GET|PUT|PATCH /catalog/products/manage/{id}/`
- **Archive**: `POST /catalog/products/manage/{id}/archive/` (Cascades to deactivate variants)
- **Publish**: `POST /catalog/products/manage/{id}/publish/`

**Create/Update Request Body:**

```json
{
  "name": "Smartphone X",
  "description": "...",
  "base_price": "999.00",
  "category": "uuid",
  "attributes": {
    "brand": "TechCo" // Key is slug, value can be ID/String/Number
  }
}
```

#### 3.2.2. Variants Management

- **List / Create**: `GET|POST /catalog/variants/manage/`
- **Detail / Update**: `GET|PUT|PATCH /catalog/variants/manage/{id}/`
- **Activate/Deactivate**: `POST /catalog/variants/manage/{id}/activate/` | `/deactivate/`
- **Adjust Stock**: `POST /catalog/variants/manage/{id}/adjust-stock/`

**Create/Update Request Body:**

```json
{
  "product": "uuid",
  "sku": "SM-X-128",
  "name": "128GB Edition",
  "base_price": "1099.00", // Optional: If null, inherits from product
  "stock_quantity": 50,
  "attributes": {
    "color": "Black"
  }
}
```

**Adjust Stock Body:**

```json
{
  "quantity_delta": -5 // Atomic row-level lock increment/decrement
}
```

#### 3.2.3. Discounts Management (Staff Only)

- **List / Create**: `GET|POST /catalog/discounts/manage/`
- **Detail / Update**: `GET|PUT|PATCH /catalog/discounts/manage/{id}/`

**Create Request Body:**

```json
{
  "name": "Black Friday",
  "discount_type": "percentage", // "percentage" or "fixed_amount"
  "value": "20.00",
  "start_date": "2026-11-20T00:00:00Z",
  "end_date": "2026-12-01T00:00:00Z", // Optional
  "categories": ["uuid"],
  "products": ["uuid"],
  "variants": ["uuid"]
}
```

---

## 4. Special Rules & Error Conditions

### 4.1 Stock Handling

Stock cannot be updated via standard PUT/PATCH. You must use the `adjust-stock` endpoint to prevent race conditions during checkout. Attempting to reduce stock below 0 via `adjust-stock` yields a `400 Bad Request` with an `insufficient_stock` error context.

### 4.2 Attributes and Fallbacks

1. Attribute JSON handling maps slugs to DB schemas dynamically. The user sees a unified array under `attributes` but passes a simple Key-Value mapping during writes.
2. Variant images automatically fall back to `Product` images via `ProductImageSerializer` if none are linked directly to the variant.

### 4.3 Catalog Error Codes

- `400` : General validation errors (e.g., percentage discount > 100%, category discount with fixed_amount).
- `400` : `insufficient_stock` - Tried to reduce below zero.
- `400` : `duplicate_sku` - Violates unique constraint on Variant sku.
- `403` : Validated via `IsOwnerOrStaff`. Returned if an owner touches a Product/Variant belonging to another profile.
- `404` : Entity missing or UUID improperly formatted.
