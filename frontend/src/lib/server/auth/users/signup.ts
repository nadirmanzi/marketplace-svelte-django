import { apiFetch } from "$lib/api/client";
import type { UserProfile } from "$lib/api/types";

/**
 * Standard Signup Result.
 */
export interface SignupResult {
    success: boolean;
    status_code: number;
    user?: UserProfile;
    error?: string;
    fieldErrors?: Record<string, string>;
}

/**
 * Creates a new account and automatically logs the user in.
 * Section 3.1 of API Guide.
 */
import type { RequestEvent } from "@sveltejs/kit";

/**
 * Creates a new account and manually forwards JWT cookies from Django to the Browser.
 */
export const signup = async (
    full_name: string,
    email: string,
    password: string,
    customFetch: typeof fetch,
    event: RequestEvent
): Promise<SignupResult> => {
    
    const { data, error, status, ok, headers } = await apiFetch<UserProfile>('/users/management/', {
        method: 'POST',
        body: JSON.stringify({ full_name, email, password })
    }, customFetch);

    // --- COOKIE FORWARDING LOGIC ---
    if (ok && headers) {
        const backendCookies = headers.getSetCookie ? headers.getSetCookie() : [];

        backendCookies.forEach(cookieString => {
            const [nameValue, ...attributes] = cookieString.split('; ');
            const [name, value] = nameValue.split('=');

            const isHttpOnly = cookieString.toLowerCase().includes('httponly');
            const isSecure = cookieString.toLowerCase().includes('secure');
            const maxAgeMatch = cookieString.match(/Max-Age=(\d+)/i);
            const maxAge = maxAgeMatch ? parseInt(maxAgeMatch[1]) : undefined;

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
                status_code: status,
                fieldErrors: {
                    email: error.errors.email?.[0] || '',
                    full_name: error.errors.full_name?.[0] || '',
                    password: error.errors.password?.[0] || ''
                }
            };
        }

        return {
            success: false,
            status_code: status,
            error: error?.detail || error?.non_field_errors?.[0] || 'Registration failed.'
        };
    }

    return {
        success: true,
        status_code: status,
        user: data || undefined
    };
};