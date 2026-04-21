import { message, superValidate } from "sveltekit-superforms";
import type { Actions, PageServerLoad } from "./$types";
import { fail, redirect } from "@sveltejs/kit";
import { zod4 } from "sveltekit-superforms/adapters";
import { signup_schema } from "$lib/schemas/auth";
import { signup } from "$lib/server/auth/users/signup";
import { guardAuth } from "$lib/server/auth/session";

export const load: PageServerLoad = async ({ locals, url }) => {
    guardAuth(locals, url);
    const form = await superValidate(zod4(signup_schema));
    return { form };
};

export const actions: Actions = {
    default: async (event) => {
        const { request } = event;
        const form = await superValidate(request, zod4(signup_schema));
        if (!form.valid) return fail(400, { form });

        const result = await signup(
            form.data.full_name,
            form.data.email,
            form.data.password,
            event.fetch,
            event
        );

        if (!result.success) {
            if (result.fieldErrors) {
                form.errors.full_name = result.fieldErrors.full_name ? [result.fieldErrors.full_name] : undefined;
                form.errors.email = result.fieldErrors.email ? [result.fieldErrors.email] : undefined;
                form.errors.password = result.fieldErrors.password ? [result.fieldErrors.password] : undefined;
                return fail(400, { form });
            }

            const status = result.status_code === 429 ? 429 : 400;

            return message(form, {
                type: 'error' as const,
                text: result.error!,
                status: status
            }, { status });
        }

        throw redirect(302, '/');
    }
};