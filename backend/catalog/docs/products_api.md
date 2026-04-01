# Product & Variant API Reference

This document covers the public viewing and management of Products and Variants in the `catalog` app.

## Architecture

*   **Product**: A concrete blueprint/template for a group of sellable items. It contains the core name, description, and base price. It is **not** directly listed for sale.
*   **ProductVariant**: The actual sellable entity. It belongs to a Product blueprint and has its own SKU, price, and stock levels.

---

## Public Endpoints (No Authentication Required)

These endpoints return only **published** products and **active** variants.

### `GET /catalog/products/`
List all published products with their active variants embedded.

**Query Filters:**
*   `name` (icontains)
*   `category` (UUID)
*   `min_price` (gte)
*   `max_price` (lte)

---

### `GET /catalog/products/{slug}/`
Retrieve a single published product and its active variants by slug.

---

## Management Endpoints (Owner or Staff Only)

Requires `Authorization: Bearer <access_token>`. Access is granted if the user is the **owner** of the product, or represents **staff/admin**.

### `GET /catalog/products/manage/`
List all products associated with the authenticated user (staff sees everything).

---

### `POST /catalog/products/manage/`
Create a new product blueprint.
```json
{
  "name": "Wireless Stereo Headset",
  "base_price": "199.99",
  "description": "Premium audio experience...",
  "category": "uuid",
  "status": "published"
}
```

---

### `POST /catalog/products/manage/{pk}/archive/`
Archive a product. This **cascades** and deactivates all associated variants.

---

### `POST /catalog/products/manage/{pk}/publish/`
Publish a previously archived product.

---

### `GET /catalog/variants/manage/`
List all variants associated with the authenticated user's products.

---

### `POST /catalog/variants/manage/`
Create a variant for a specific product.
```json
{
  "product": "uuid",
  "sku": "HEADSET-BLK-01",
  "name": "Midnight Black",
  "price": "199.99",
  "stock_quantity": 50,
  "metadata": {"color": "black", "material": "plastic"}
}
```

---

### `POST /catalog/variants/manage/{pk}/adjust-stock/`
Atomically adjust stock quantity. Uses **row-level locking** (`SELECT FOR UPDATE`) to prevent race conditions.
```json
{
  "quantity_delta": -5
}
```

---

### `POST /catalog/variants/manage/{pk}/deactivate/`
Deactivate a specific variant.

---

### `POST /catalog/variants/manage/{pk}/activate/`
Re-activate a specific variant.
