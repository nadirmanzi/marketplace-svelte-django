import { apiFetch } from "$lib/api/client";
import type { LoginResponse } from "$lib/api/types";
import type { RequestEvent } from "@sveltejs/kit";

/**
 * Standard Login Result.
 */
export interface LoginResult {
    success: boolean;
    user?: { user_id: string; email: string };
    error?: string;
    code?: string;
    fieldErrors?: Record<string, string>;
}

/**
 * Authenticates user and manually forwards JWT cookies from Django to the Browser.
 */
export const login = async (
    email: string,
    password: string,
    customFetch: typeof fetch,
    event: RequestEvent
): Promise<LoginResult> => {

    // We pass event.request.headers to ensure any existing context is sent to Django,
    // and we use event.fetch (customFetch) which is SvelteKit's specialized fetch.
    const { data, error, status, ok, headers } = await apiFetch<LoginResponse>(
        '/users/auth/login/',
        {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        },
        customFetch
    );

    // --- COOKIE FORWARDING LOGIC ---
    // If the request was successful and we have headers, we must bridge the gap
    // between the Django response and the Browser response.
    if (ok && headers) {
        // .getSetCookie() is the modern way to get multiple Set-Cookie headers
        const backendCookies = headers.getSetCookie ? headers.getSetCookie() : [];

        backendCookies.forEach(cookieString => {
            // Parse the "key=value; Attribute; Attribute" string
            const [nameValue, ...attributes] = cookieString.split('; ');
            const [name, value] = nameValue.split('=');

            // Detect attributes for SvelteKit's cookie options
            const isHttpOnly = cookieString.toLowerCase().includes('httponly');
            const isSecure = cookieString.toLowerCase().includes('secure');

            // Extract Max-Age if present (e.g., "Max-Age=600")
            const maxAgeMatch = cookieString.match(/Max-Age=(\d+)/i);
            const maxAge = maxAgeMatch ? parseInt(maxAgeMatch[1]) : undefined;

            // Set the cookie in SvelteKit. This header will now be 
            // included in the response sent to the user's browser.
            event.cookies.set(name, value, {
                path: '/',
                httpOnly: isHttpOnly,
                secure: isSecure,
                sameSite: 'lax',
                maxAge: maxAge
            });
        });
    }

    if (!ok) {
        if (status === 400 && error?.errors) {
            return {
                success: false,
                fieldErrors: {
                    email: error.errors.email?.[0] || '',
                    password: error.errors.password?.[0] || ''
                }
            };
        }

        // Handle 403 Forbidden - Password Expired
        if (status === 403 && error?.code === 'password_expired') {
            return {
                success: true,
                user: error.user,
                code: 'password_expired',
                error: error.detail
            };
        }

        // Handle 429 Too Many Requests
        if (status === 429) {
            return { success: false, code: 'throttled', error: error?.detail };
        }

        return {
            success: false,
            error: error?.detail || error?.non_field_errors?.[0] || 'Authentication failed.'
        };
    }

    return {
        success: true,
        user: data?.user
    };
};