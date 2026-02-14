<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button/index.js';

	let { href, label, children }: { href: string; label: string; children?: any } = $props();

	const is_active = page.url.pathname === href;
</script>

<Button {href} variant={is_active ? 'secondary' : 'ghost'} size="sm">
	{#if children}
		{@render children?.()}
	{:else}
		<p>
			{label}
		</p>
	{/if}
</Button>

<style>
</style>
