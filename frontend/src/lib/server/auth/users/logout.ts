import { apiFetch } from "$lib/api/client";

/**
 * Logs the user out and invalidates the session on the backend.
 * Section 3.5 of API Guide.
 */
export const logout = async (customFetch: typeof fetch): Promise<boolean> => {
    const { ok } = await apiFetch('/users/auth/logout/', { method: 'POST' }, customFetch);
    return ok;
};
