import { apiFetch } from "../client";
import type { ProductBlueprint, ProductVariant } from "./types";

/**
 * Creates a new product blueprint.
 * Section 5.1 of Catalog API Guide.
 */
export async function createProduct(
    data: {
        name: string;
        description: string;
        base_price: string;
        category: string;
        attributes: Record<string, any>;
    },
    customFetch: typeof fetch = fetch
) {
    return apiFetch<ProductBlueprint>('/catalog/products/manage/', {
        method: 'POST',
        body: JSON.stringify(data)
    }, customFetch);
}

/**
 * Publish a product blueprint.
 * Section 5.2 of Catalog API Guide.
 */
export async function publishProduct(productId: string, customFetch: typeof fetch = fetch) {
    return apiFetch<ProductBlueprint>(`/catalog/products/manage/${productId}/publish/`, {
        method: 'POST'
    }, customFetch);
}

/**
 * Archive a product blueprint.
 * Section 5.2 of Catalog API Guide.
 */
export async function archiveProduct(productId: string, customFetch: typeof fetch = fetch) {
    return apiFetch<ProductBlueprint>(`/catalog/products/manage/${productId}/archive/`, {
        method: 'POST'
    }, customFetch);
}

/**
 * Atomically adjust variant stock.
 * Section 6.1 of Catalog API Guide.
 */
export async function adjustStock(
    variantId: string,
    quantityDelta: number,
    customFetch: typeof fetch = fetch
) {
    return apiFetch<ProductVariant>(`/catalog/variants/manage/${variantId}/adjust-stock/`, {
        method: 'POST',
        body: JSON.stringify({ quantity_delta: quantityDelta })
    }, customFetch);
}
