<script lang="ts">
	import { page } from '$app/state';
	import { Button } from '$lib/components/ui/button/index';

	let { href, label, children }: { href: string; label: string; children?: any } = $props();

	const IS_ACTIVE = $derived(page.url.pathname === href);
</script>

<Button {href} variant={IS_ACTIVE ? 'secondary-outline' : 'ghost-ghost'} size="sm">
	{#if children}
		{@render children?.()}
	{:else}
		<p>
			{label}
		</p>
	{/if}
</Button>
