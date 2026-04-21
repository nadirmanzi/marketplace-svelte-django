import { apiFetch } from "$lib/api/client";
import type { UserProfile } from "$lib/api/types";
import { redirect, type RequestEvent } from "@sveltejs/kit";
import { forwardCookies } from "./cookies";

/**
 * SESSION MANAGEMENT & IDENTITY MODULE
 * 
 * This module consolidates all logic related to session verification, 
 * identity resolution, and token rotation. 
 */

/**
 * Retrieves the full profile of the currently logged-in user.
 * Bridges identity from cookies to internal API headers if an accessToken is provided.
 */
export const getUserProfile = async (
    customFetch: typeof fetch,
    accessToken?: string
): Promise<UserProfile | null> => {
    const res = await apiFetch<UserProfile>(
        '/users/management/me/',
        { method: 'GET', authToken: accessToken },
        customFetch
    );
    return res.ok ? res.data : null;
};

/**
 * Verifies the validity of an access token against the backend.
 */
export const verifyToken = async (
    customFetch: typeof fetch, 
    accessToken?: string
): Promise<boolean> => {
    const { ok } = await apiFetch(
        '/users/auth/token/verify/',
        { method: 'POST', authToken: accessToken },
        customFetch
    );
    return ok;
};

/**
 * Performs a sliding session refresh (token rotation).
 * Bridges identity from cookies to ensure internal Docker requests are authenticated.
 */
export const refreshToken = async (event: RequestEvent): Promise<boolean> => {
    const refresh_token = event.cookies.get('refresh_token');
    
    const { ok, headers } = await apiFetch('/users/auth/token/refresh/', {
        method: 'POST',
        refreshCookie: refresh_token
    }, event.fetch);

    if (ok && headers) {
        forwardCookies(headers, event);
        return true;
    }

    return false;
};

/**
 * Helper to retrieve a guarded user session. Redirects to login if not authenticated.
 */
export const getSession = (locals: App.Locals, url: URL) => {
    if (!locals.is_authenticated || !locals.user) {
        redirect(302, `/auth/login?next=${encodeURIComponent(url.pathname)}`);
    }
    return locals.user;
};

/**
 * Helper to guard auth-only routes (like Login/Signup). Redirects to homepage if already logged in.
 */
export const guardAuth = (locals: App.Locals, url: URL) => {
    if (locals.is_authenticated) {
        const next = sanitizeNext(url.searchParams.get('next'));
        redirect(302, next);
    }
};

/**
 * Standardizes sanitization for redirect 'next' parameters.
 */
export const sanitizeNext = (next: string | null): string => {
    if (!next) return '/';
    // Prevent open redirect vulnerabilities by ensuring it starts with / and not //
    if (!next.startsWith('/') || next.startsWith('//')) return '/';
    return next;
};
