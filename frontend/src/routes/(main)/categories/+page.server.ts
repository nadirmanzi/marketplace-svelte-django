import { getCategoryTree } from '$lib/api/catalog/categories';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const { data: categories, error } = await getCategoryTree(fetch);

	console.log({ categories });

	return { categories: categories || [] };
};
