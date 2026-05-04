import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
	return {
		is_authenticated: locals.is_authenticated,
		user: locals.user
	};
};
