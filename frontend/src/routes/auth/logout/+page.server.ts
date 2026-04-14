import type { Actions } from "./$types";
import { logout } from "$lib/server/auth/users/logout";
import { redirect } from "@sveltejs/kit";

export const actions: Actions = {
    default: async (event) => {
        const result = await logout(event.fetch);
        if (!result) {
            return { error: 'Logout failed' };
        }
        return redirect(302, '/auth/login');
    }
};