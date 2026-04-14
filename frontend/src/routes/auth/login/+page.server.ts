import { message, superValidate } from "sveltekit-superforms";
import type { Actions, PageServerLoad } from "./$types";
import { fail } from "@sveltejs/kit";
import { zod4 } from "sveltekit-superforms/adapters";
import { login_schema } from "$lib/schemas/auth";
import { login } from "$lib/server/auth/users/login";

import { redirect } from "@sveltejs/kit";
import { guardAuth } from "$lib/server/auth/users/session";

export const load: PageServerLoad = async ({ url, locals, }) => {
    guardAuth(locals, url);
    const form = await superValidate(zod4(login_schema));
    return { form, next: url.searchParams.get('next') ?? '/' };
};

export const actions: Actions = {
    // We take the full 'event' object here
    default: async (event) => {
        const { request, url } = event;

        const form = await superValidate(request, zod4(login_schema));
        if (!form.valid) return fail(400, { form });

        // 1. Pass 'event' so the login function can set cookies
        // 2. Use 'event.fetch' instead of global 'fetch' for better SvelteKit integration
        const result = await login(
            form.data.email,
            form.data.password,
            event.fetch,
            event
        );

        if (!result.success) {
            if (result.fieldErrors) {
                form.errors.email = result.fieldErrors.email ? [result.fieldErrors.email] : undefined;
                form.errors.password = result.fieldErrors.password ? [result.fieldErrors.password] : undefined;
                return fail(400, { form });
            }

            if (result.code === 'throttled') {
                return message(form, {
                    type: 'error' as const,
                    text: 'Too many requests! Try again later.',
                    status: 429
                }, { status: 429 });
            }

            return message(form, {
                type: 'error' as const,
                text: result.error || 'Authentication failed'
            }, { status: 401 });
        }

        // Handle expired password logic
        if (result.code === 'password_expired') {
            throw redirect(302, '/auth/change-password');
        }

        // Success redirect
        const next = url.searchParams.get('next') ?? '/';
        throw redirect(302, next);
    }
};