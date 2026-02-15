<script lang="ts">
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Menu } from '@lucide/svelte';

	type Link = {
		href: string;
		label: string;
	};

	let { links }: { links: Link[] } = $props();
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger variant="ghost" size="icon">
		<Menu class="size-5" />
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-56">
		<DropdownMenu.Label>Navigation</DropdownMenu.Label>
		<DropdownMenu.Separator />
		{#each links as link}
			<a href={link.href}>
				<DropdownMenu.Item>{link.label}</DropdownMenu.Item>
			</a>
		{/each}
	</DropdownMenu.Content>
</DropdownMenu.Root>
