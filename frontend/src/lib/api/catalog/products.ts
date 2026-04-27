import { apiFetch } from "../client";
import type { ProductBlueprint, ProductFilter } from "./types";
import type { ProductListResponse, ProductDetailResponse } from "$lib/api/types";

/**
 * Public listing of products with filtering.
 * Section 4.1 of Catalog API Guide.
 */
export async function listProducts(
    filters: ProductFilter = {},
    customFetch: typeof fetch = fetch
) {
    const params: Record<string, string> = {};
    if (filters.category) params.category = filters.category;
    if (filters.min_price) params.min_price = String(filters.min_price);
    if (filters.max_price) params.max_price = String(filters.max_price);
    if (filters.name) params.name = filters.name;
    if (filters.page) params.page = String(filters.page);
    if (filters.page_size) params.page_size = String(filters.page_size);

    return apiFetch<ProductListResponse>('/catalog/products/', { params }, customFetch);
}

/**
 * Get full details of a single product by slug.
 * Section 4.2 of Catalog API Guide.
 */
export async function getProductDetail(slug: string, customFetch: typeof fetch = fetch) {
    return apiFetch<ProductDetailResponse>(`/catalog/products/${slug}/`, { method: 'GET' }, customFetch);
}
