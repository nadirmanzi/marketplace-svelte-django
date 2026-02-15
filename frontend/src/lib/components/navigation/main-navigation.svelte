<script lang="ts">
	import { Search } from '@lucide/svelte';
	import NavLink from '$lib/components/navigation/nav-link.svelte';
	import NavMenuDropdown from '$lib/components/navigation/nav-menu-dropdown.svelte';
	import NavCartSheet from '$lib/components/navigation/nav-cart-sheet.svelte';
	import TopNavigation from './top-navigation.svelte';
	import Button from '../ui/button/button.svelte';
	import { flip } from 'svelte/animate';

	type NAVIGATION_LINK_TYPES = {
		href: string;
		label: string;
	};
	const NAVIGATION_LINKS: NAVIGATION_LINK_TYPES[] = [
		{ href: '/', label: 'Home' },
		{ href: '/browse', label: 'Browse' },
		{ href: '/categories', label: 'Categories' },
		{ href: '/verified-vendors', label: 'Verified vendors' },
		{ href: '/track-order', label: 'Track order' }
	];
</script>

<TopNavigation>
	<div class="flex">
		{#each NAVIGATION_LINKS as { href, label } (href)}
			<!-- <div class="" animate:flip> -->
			<NavLink {href} {label} />
			<!-- </div> -->
		{/each}
	</div>
	<div class=" space-x-0">
		<Button variant="ghost-ghost" size="icon-sm">
			<Search class="size-4" strokeWidth={1.8} />
		</Button>

		<NavCartSheet />
		<NavMenuDropdown />
	</div>

	<!-- {#snippet end()}
		<div class="flex h-full items-center justify-end space-x-4">
			<InputGroup.Root class="">
				<InputGroup.Input placeholder="Search..." />
				<InputGroup.Addon align="inline-start">
					<Search class="size-4" strokeWidth={1.8} />
				</InputGroup.Addon>
			</InputGroup.Root>

			<Separator orientation="vertical" />

			<div class="">
				<CartSheet />
				<NavMenuDropdown />
			</div>
		</div>
	{/snippet} -->
</TopNavigation>
