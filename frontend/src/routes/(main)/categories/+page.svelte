<script lang="ts">
	import type { PageProps } from './$types';
	import type { CategoryNode } from '$lib/api/catalog/types';

	let { data }: PageProps = $props();

	const categories = $derived(data.categories);
</script>

{#snippet CategoryItem(category: CategoryNode, depth = 0)}
	<div class="">
		<p>{category.name}</p>

		<div class="px-2 text-nav-foreground-muted">
			{#if category.children.length > 0}
				{#each category.children as subcategory (subcategory.category_id)}
					{@render CategoryItem(subcategory, depth + 1)}
				{/each}
			{/if}
		</div>
	</div>
{/snippet}

<div class="mx-auto max-w-7xl px-8 py-24">
	<header class="mb-20 space-y-4">
		<h1 class="font-display text-5xl font-black tracking-tighter text-white sm:text-7xl">
			Categories
		</h1>
		<p class="max-w-2xl text-lg text-nav-foreground-muted">
			Browse our extensive collection of products organized by category. From hand-crafted goods to
			cutting-edge technology.
		</p>
	</header>

	<div class="space-y-5">
		{#if categories}
			{#each categories as category (category.category_id)}
				{@render CategoryItem(category)}
			{/each}
		{:else}
			<div
				class="flex min-h-[400px] flex-col items-center justify-center space-y-4 rounded-3xl border border-dashed border-white/10"
			>
				<p class="text-nav-foreground-muted">No categories found.</p>
			</div>
		{/if}
	</div>
</div>
