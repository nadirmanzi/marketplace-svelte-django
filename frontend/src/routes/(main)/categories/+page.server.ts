import { getCategoryTree } from '$lib/api/catalog/categories';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
	const { data, } = await getCategoryTree(fetch);

	const categories = data?.data.categories

	console.log(categories)

	return { categories: categories || [] };
};
