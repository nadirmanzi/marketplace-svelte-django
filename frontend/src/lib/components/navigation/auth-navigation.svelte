<script lang="ts">
	import { ChevronRight, LogIn, Search, ShoppingBag, Store, User, UserPlus } from '@lucide/svelte';
	import NavLink from '$lib/components/navigation/nav-link.svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index';
	import NavMenuDropdown from '$lib/components/navigation/nav-menu-dropdown.svelte';
	import NavCartSheet from '$lib/components/navigation/nav-cart-sheet.svelte';
	import Separator from '$lib/components/ui/separator/separator.svelte';
	import Logo from '../logo.svelte';
	import { flip } from 'svelte/animate';

	const NAVIGATION_LINKS = [
		{ href: '/auth/login', label: 'Login' },
		{ href: '/auth/register', label: 'Register' },
		{ href: '/auth/register/seller', label: 'Become a seller' }
	];
</script>

<nav
	class={`relative flex h-16 w-full items-center justify-between px-4 bg-nav-background text-foreground`}
>
	<!-- LOGO & MAIN LINKS -->
	<div class="flex items-center justify-center space-x-16">
		<!-- LOGO -->
		<div class="flex items-center">
			<a href="/">
				<Logo variant="primary" class="" />
			</a>
		</div>

		<!-- MAIN LINKS -->
		<div class="absolute top-1/2 left-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center">
			{#each NAVIGATION_LINKS as { href, label } (href)}
				<NavLink {href} {label}></NavLink>
			{/each}
		</div>
	</div>
</nav>

<style>
	nav {
		view-transition-name: auth-navigation;
	}
</style>
