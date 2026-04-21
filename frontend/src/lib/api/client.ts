import { env } from "$env/dynamic/private";
import type { ApiError, ApiResult } from "./types";

export interface ApiFetchOptions extends RequestInit {
    params?: Record<string, string>;
    authToken?: string;     // Manual Bearer token for server-side bridging
    refreshCookie?: string; // Manual refresh cookie for server-side bridging
}

/**
 * Centralized fetch wrapper for the Marketplace API.
 * 
 * Implements core requirements:
 * - credentials: 'include'
 * - Trailing slashes
 * - Standardized error handling via ApiResult union
 */
export async function apiFetch<T>(
    path: string,
    options: ApiFetchOptions = {},
    customFetch: typeof fetch = fetch
): Promise<ApiResult<T>> {

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

    // 2.1 Manual Token Bridging (for server-side internal calls)
    if (options.authToken) {
        headers.set('Authorization', `Bearer ${options.authToken}`);
    }
    if (options.refreshCookie) {
        headers.set('Cookie', `refresh_token=${options.refreshCookie}`);
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
            return { ok: true, status: 204, data: null as any, headers: response.headers, error: null };
        }

        const contentType = response.headers.get('content-type');
        const isJson = contentType?.includes('application/json');
        
        // Only attempt to parse JSON if content-type says so
        let body: any = null;
        if (isJson) {
            try {
                body = await response.json();
            } catch (e) {
                body = null;
            }
        }

        if (!response.ok) {
            // Build a valid ApiError even if backend failed or returned non-JSON
            const error: ApiError = {
                success: false,
                code: body?.code || 'server_error',
                detail: body?.detail || `Request failed with status ${response.status}`,
                errors: body?.errors || {}
            };

            return {
                ok: false,
                status: response.status,
                error,
                data: null,
                headers: response.headers
            };
        }

        return {
            ok: true,
            status: response.status,
            data: body as T,
            error: null,
            headers: response.headers
        };
    } catch (err) {
        return {
            ok: false,
            status: 500,
            error: {
                success: false,
                code: 'connection_error',
                detail: 'Backend service unreachable.',
                errors: {}
            },
            data: null,
            headers: null
        };
    }
}
