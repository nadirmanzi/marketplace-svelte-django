import { apiFetch } from "$lib/api/client";
import type { UserProfile } from "$lib/api/types";

/**
 * Retrieves the full profile of the currently logged-in user.
 * Section 3.7 of API Guide.
 */
export const getUserProfile = async (customFetch: typeof fetch): Promise<UserProfile | null> => {
    const { data, ok } = await apiFetch<UserProfile>('/users/management/me/', { method: 'GET' }, customFetch);
    return ok ? data : null;
};
