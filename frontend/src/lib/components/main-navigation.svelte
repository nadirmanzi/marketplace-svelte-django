<script lang="ts">
	import { ChevronRight, LogIn, Search, ShoppingBag, Store, User, UserPlus } from '@lucide/svelte';
	import { slide } from 'svelte/transition';
	import NavLink from './nav-link.svelte';
	import { sineOut } from 'svelte/easing';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import CartSheet from './cart-sheet.svelte';
	import NavUserDropdown from './nav-user-dropdown.svelte';

	let is_searchbar_open = $state(false);

	type NAVIGATION_LINK_TYPES = {
		href: string;
		label: string;
	};

	// const NAVIGATION_LINKS: NAVIGATION_LINK_TYPES[] = [
	// 	{ href: '/', label: 'Shop', icon: Store },
	// 	{ href: '/sellers', label: 'Sellers', icon: Store },
	// 	{ href: '/categories', label: 'Categories', icon: Store },
	// 	{ href: '/track-order', label: 'Track order', icon: Store },
	// 	{ href: '/auth/login', label: 'My account', icon: Store },
	// 	{ href: '/auth/faq', label: 'Help', icon: Store }
	// ];
	const NAVIGATION_LINKS: NAVIGATION_LINK_TYPES[] = [
		{ href: '/', label: 'Home' },
		{ href: '/browse', label: 'Browse' },
		{ href: '/track-order', label: 'Track order' },
		{ href: '/help-center', label: 'Help center' },
		{ href: '/auth/register/seller', label: 'Become a seller' }
	];
</script>

<nav
	class={`sticky top-0 z-50 w-full border-b border-nav-border bg-nav-background text-nav-foreground`}
>
	<section class="flex h-14 w-full items-center justify-between px-4">
		<!-- LOGO & MAIN LINKS -->
		<div class="flex items-center justify-center space-x-16">
			<!-- LOGO -->
			<div class="flex items-center">
				<a href="/">
					<img src="/primary-logo.svg" alt="Primary logo" class="h-8 w-8" />
				</a>
			</div>

			<!-- MAIN LINKS -->
			<div class="flex items-center space-x-1">
				{#each NAVIGATION_LINKS as { href, label }}
					<NavLink {href} {label}></NavLink>
				{/each}
			</div>
		</div>

		<!-- ACTION BUTTONS & SEARCH -->
		<div class="flex h-full items-center justify-end space-x-4">
			<!-- SEARCH -->
			<InputGroup.Root class="">
				<InputGroup.Input placeholder="Search..." />
				<InputGroup.Addon align="inline-start">
					<Search class="size-4" strokeWidth={1.8} />
				</InputGroup.Addon>
			</InputGroup.Root>

			<!-- SEPARATOR -->
			<Separator orientation="vertical" />

			<div class="">
				<!-- SHOPPING BAG -->
				<CartSheet />
				<!-- USER DROPDOWN-->
				<NavUserDropdown />
			</div>
		</div>
	</section>

	<!-- SEARCH BAR -->
	<!-- {#if !is_searchbar_open}
		<section
			in:slide={{ axis: 'y', duration: 300, easing: sineOut }}
			out:slide={{ axis: 'y', duration: 300, easing: sineOut }}
			class="h-14 w-full rounded-xl"
		>
			<div class="flex h-16 w-full items-center justify-center p-2">
				<Input class="" />
			</div>
		</section>
	{/if} -->
</nav>
