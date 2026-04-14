import { env } from "$env/dynamic/private";
import type { ApiError } from "./types";

export interface ApiFetchOptions extends RequestInit {
    params?: Record<string, string>;
}

/**
 * Centralized fetch wrapper for the Marketplace API.
 * 
 * Implements core requirements from the Authentication API Guide:
 * - credentials: 'include' (Section 1.1)
 * - Trailing slashes (Section 1.2 usage)
 * - Standardized error handling (Section 5)
 */
export async function apiFetch<T>(
    path: string,
    options: ApiFetchOptions = {},
    customFetch: typeof fetch = fetch
): Promise<{ data: T | null; error: ApiError | null; status: number; ok: boolean, headers: Headers | null }> {

    // 1. URL Normalization
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    const urlPath = normalizedPath.endsWith('/') ? normalizedPath : `${normalizedPath}/`;

    let url = `${env.BACKEND_URL || ''}${urlPath}`;

    if (options.params) {
        const searchParams = new URLSearchParams(options.params);
        url += `?${searchParams.toString()}`;
    }

    // 2. Request Configuration
    const headers = new Headers(options.headers);
    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
        headers.set('Content-Type', 'application/json');
    }

    const fetchOptions: RequestInit = {
        ...options,
        headers,
        credentials: 'include',
    };

    try {
        const response = await customFetch(url, fetchOptions);

        // Handle 204 No Content
        if (response.status === 204) {
            return { data: null, error: null, status: 204, ok: true, headers: response.headers };
        }

        const isJson = response.headers.get('content-type')?.includes('application/json');
        const body = isJson ? await response.json() : null;

        if (!response.ok) {
            return {
                data: null,
                error: body as ApiError,
                status: response.status,
                ok: false,
                headers: response.headers
            };
        }

        return {
            data: body as T,
            error: null,
            status: response.status,
            ok: true,
            headers: response.headers
        };
    } catch (err) {
        return {
            data: null,
            error: { detail: 'Backend service unreachable.' },
            status: 500,
            ok: false,
            headers: null
        };
    }
}
