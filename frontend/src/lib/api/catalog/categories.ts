import { apiFetch } from "../client";
import type { Category, CategoryNode, CategoryAttribute } from "./types";

/**
 * List categories (flat).
 * Section 3.1 of Catalog API Guide.
 */
export async function listCategories(
    params: { name?: string; is_root?: boolean } = {},
    customFetch: typeof fetch = fetch
) {
    const queryParams: Record<string, string> = {};
    if (params.name) queryParams.name = params.name;
    if (params.is_root !== undefined) queryParams.is_root = String(params.is_root);

    return apiFetch<Category[]>('/catalog/categories/', { params: queryParams }, customFetch);
}

/**
 * Get category tree (nested).
 * Section 3.2 of Catalog API Guide.
 */
export async function getCategoryTree(customFetch: typeof fetch = fetch) {
    return apiFetch<CategoryNode[]>('/catalog/categories/', { method: 'GET' }, customFetch);
}

/**
 * Get attributes required for a category.
 * Section 3.3 of Catalog API Guide.
 */
export async function getCategoryAttributes(categoryId: string, customFetch: typeof fetch = fetch) {
    return apiFetch<CategoryAttribute[]>(`/catalog/categories/${categoryId}/attributes/`, { method: 'GET' }, customFetch);
}
