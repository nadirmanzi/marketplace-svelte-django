import { apiFetch } from "$lib/api/client";
import type { RequestEvent } from "@sveltejs/kit";

/**
 * Verifies the current access token stored in cookies.
 * Section 3.4 of API Guide.
 */
export const verifyToken = async (customFetch: typeof fetch): Promise<boolean> => {
    const { ok } = await apiFetch('/users/auth/token/verify/', { method: 'POST' }, customFetch);
    return ok;
};

/**
 * Refreshes the access token and manually updates the SvelteKit cookie jar.
 */
export const refreshToken = async (event: import("@sveltejs/kit").RequestEvent): Promise<boolean> => {
    // 1. Call the API using event.fetch
    const { ok, headers } = await apiFetch('/users/auth/token/refresh/', {
        method: 'POST'
    }, event.fetch);

    // 2. If Django sent new tokens, we MUST relay them to the browser
    if (ok && headers) {
        const backendCookies = headers.getSetCookie ? headers.getSetCookie() : [];

        backendCookies.forEach(cookieString => {
            const [nameValue, ...attributes] = cookieString.split('; ');
            const [name, value] = nameValue.split('=');

            const isHttpOnly = cookieString.toLowerCase().includes('httponly');
            const isSecure = cookieString.toLowerCase().includes('secure');
            const maxAgeMatch = cookieString.match(/Max-Age=(\d+)/i);
            const maxAge = maxAgeMatch ? parseInt(maxAgeMatch[1]) : undefined;

            // Update the cookie store so the REST of the hook can see it
            event.cookies.set(name, value, {
                path: '/',
                httpOnly: isHttpOnly,
                secure: isSecure,
                sameSite: 'lax',
                maxAge: maxAge
            });
        });

        return true;
    }

    return false;
};