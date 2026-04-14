<script lang="ts">
	/*
	 * ─── MAIN NAV LINKS ─────────────────────────────────────────────────────────
	 * This component renders the individual navigation links in the top bar.
	 * It manages a single "Sliding Pill" that follows the mouse across link items.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import type { Component, Snippet } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import { page } from '$app/state';
	import { expoOut, quartIn } from 'svelte/easing';
	import { auth_state } from '$lib/client/state/auth.svelte';

	// Icon Imports
	import Package from '@tabler/icons-svelte-runes/icons/package';
	import Receipt from '@tabler/icons-svelte-runes/icons/receipt';
	import Exchange from '@tabler/icons-svelte-runes/icons/exchange';
	import Heart from '@tabler/icons-svelte-runes/icons/heart';
	import User from '@tabler/icons-svelte-runes/icons/user';
	import ShieldLock from '@tabler/icons-svelte-runes/icons/shield-lock';
	import CreditCard from '@tabler/icons-svelte-runes/icons/credit-card';
	import BellRinging from '@tabler/icons-svelte-runes/icons/bell-ringing';

	// Component UI Imports
	import AnimatedPillGroup from '../ui/animated-pill-group.svelte';
	import AnimatedPillItem from '../ui/animated-pill-item.svelte';
	import UserPlus from '@tabler/icons-svelte-runes/icons/user-plus';
	import Login from '@tabler/icons-svelte-runes/icons/login';
	import Button from '../ui/button.svelte';
	import HandGrab from '@tabler/icons-svelte-runes/icons/hand-grab';
	import HandOff from '@tabler/icons-svelte-runes/icons/hand-off';
	import TruckDelivery from '@tabler/icons-svelte-runes/icons/truck-delivery';
	import { fadeScale } from '$lib/utils/transitions.svelte';

	// ─── TRANSITIONS ─────────────────────────────────────────────────────────────
	function gracefulIn(t: number): number {
		return 1 - Math.pow(1 - t, 4); // Quartic Out
	}

	function gracefulOut(t: number): number {
		return Math.pow(t, 3); // Cubic In
	}

	// ─── PROPS ───────────────────────────────────────────────────────────────────
	interface NavLink {
		label: string;
		href?: string;
		render?: Snippet;
		description?: string;
	}

	let {
		onHover, // Global callback to tell Parent which link is active
		activeLinkLabel, // The label currently managed by Parent's state
		isOpen // Whether the Mega-Menu is currently expanded
	}: {
		onHover: (link: NavLink) => void;
		activeLinkLabel?: string;
		isOpen?: boolean;
	} = $props();

	// ─── LINK DEFINITIONS ────────────────────────────────────────────────────────
	// Central source of truth for the primary navigation categories.
	let links: NavLink[] = $derived([
		{
			label: 'Shop',
			href: '/',
			render: ShopContent,
			description: 'Discover the full marketplace and our latest arrivals.'
		},
		{
			label: 'Categories',
			href: '/categories',
			render: CategoriesContent,
			description: 'Browse an extensive range of products across all categories.'
		},
		{
			label: 'Orders',
			href: '/orders',
			render: OrdersContent,
			description: 'Track your shopping journey and manage your past purchases.'
		},
		{
			label: 'Support',
			href: '/support',
			render: SupportContent,
			description: 'Need help? Get in touch with our team or browse the FAQ.'
		},
		...(auth_state.is_authenticated
			? [
					{
						label: 'Account',
						render: AccountContent,
						description: 'Personalize your experience and manage security settings.'
					}
				]
			: [
					{
						label: 'Login/Signup',
						href: '/auth/login',
						description: 'Join [marketplace] or log into an existing account'
					}
				])
	]);

	// ─── PILL TRACKING LOGIC ─────────────────────────────────────────────────────
	let hoveredLink = $state<string | null>(null);
	let navContainer: HTMLElement;
	let pillStyle = $state('');
	let hoverTimeout: ReturnType<typeof setTimeout> | null = null;
	let mounted = $state(false);

	/**
	 * activePillId determines exactly where the sliding background pill should be.
	 * Priority: Hover state -> Global Open state -> Current Page path.
	 */
	let activePillId = $derived(
		hoveredLink ??
			(isOpen ? activeLinkLabel : null) ??
			links.find((l) =>
				l.label === 'Login/Signup'
					? page.url.pathname.startsWith('/auth')
					: page.url.pathname === l.href
			)?.label
	);

	$effect(() => {
		mounted = true;
	});

	/** Calculates intentional hover delay before triggering the Parent's state */
	function handleMouseEnter(link: NavLink) {
		if (hoverTimeout) clearTimeout(hoverTimeout);
		hoverTimeout = setTimeout(() => {
			hoveredLink = link.label;
			onHover(link);
		}, 100); // 300ms intent delay
	}

	function handleMouseLeave() {
		if (hoverTimeout) clearTimeout(hoverTimeout);
		hoverTimeout = setTimeout(() => {
			hoveredLink = null;
		}, 100);
	}

	/** Effect to measure and bind the Sliding Pill's position */
	$effect(() => {
		if (!navContainer || !activePillId || !mounted) {
			pillStyle = '';
			return;
		}

		// Find the button wrapper corresponding to the activePillId
		const activeEl = navContainer.querySelector(`[data-link-id="${activePillId}"]`) as HTMLElement;

		if (activeEl) {
			const rect = activeEl.getBoundingClientRect();
			const containerRect = navContainer.getBoundingClientRect();
			const left = rect.left - containerRect.left;
			const width = rect.width;

			pillStyle = `
				width: ${width}px;
				transform: translateX(${left}px);
			`;
		} else {
			pillStyle = '';
		}
	});
</script>

<!-- 
	─── LINK CONTENT SNIPPETS ─── 
	These snippets define the "empty canvas" for each category's mega-menu content.
-->

<!-- Reusable Column snippet for simple vertical lists -->
{#snippet ListColumn({ title, items }: { title: string; items: string[] })}
	<div class="space-y-4">
		<h3
			class="px-4 font-display text-[10px] font-bold tracking-[0.2em] text-nav-foreground-muted uppercase"
		>
			{title}
		</h3>
		<AnimatedPillGroup color="bg-nav-bg-hover">
			<div class="flex flex-col">
				{#each items as item, i (item)}
					<AnimatedPillItem id={item} class="px-4 py-2">
						<p class="text-[14px] text-nav-foreground transition-colors group-hover:text-white">
							{item}
						</p>
					</AnimatedPillItem>
				{/each}
			</div>
		</AnimatedPillGroup>
	</div>
{/snippet}

<!-- Reusable Grid snippet for "Actionable" card-style items -->
{#snippet ActionCard(items: { title: string; href?: string; desc: string; icon: Component }[])}
	<AnimatedPillGroup color="bg-nav-bg-hover">
		<div class="grid w-full grid-cols-3 gap-4">
			{#each items as item, i (item)}
				{@const Icon = item.icon}
				{@const enterStagger = 20}
				{@const exitStagger = 10}
				{@const exitBuffer = 200}
				{@const distance = 5}

				<AnimatedPillItem
					href={item.href ?? '#'}
					id={item.title}
					class="group relative flex w-full items-center p-2"
					activeClass=""
					inactiveClass=""
				>
					<div class="flex items-center gap-4">
						<div
							class="flex size-10 shrink-0 items-center justify-center rounded-full bg-nav-bg-muted text-nav-foreground transition-all group-hover:bg-transparent"
						>
							<Icon class="size-5" stroke={1.5} />
						</div>
						<div class="flex flex-col gap-0.5">
							<p class="text-sm font-semibold text-nav-foreground">{item.title}</p>
							<p class="line-clamp-1 text-[12px] text-nav-foreground-muted">{item.desc}</p>
						</div>
					</div>
				</AnimatedPillItem>
			{/each}
		</div>
	</AnimatedPillGroup>
{/snippet}

<!-- Content Definitions -->
{#snippet ShopContent()}
	<div class="grid w-full grid-cols-3 gap-8">
		{@render ListColumn({
			title: 'Featured',
			items: ['New Arrivals', 'Best Sellers', 'Trending Now']
		})}
		{@render ListColumn({ title: 'Collections', items: ['Eco-friendly', 'Handmade', 'Vintage'] })}
		{@render ListColumn({ title: 'Deals', items: ['Active discounts', 'Bundle deals'] })}
	</div>
{/snippet}

{#snippet CategoriesContent()}
	<div class="grid grid-cols-3 gap-y-12">
		{@render ListColumn({
			title: 'Home & Living',
			items: ['Furniture & decor', 'Kitchen', 'Bathroom']
		})}
		{@render ListColumn({
			title: 'Tech & Gadgets',
			items: ['Phones', 'Laptops', 'Tech Accessories']
		})}
		{@render ListColumn({ title: 'Personal care', items: ['Skincare', 'Perfumes', 'Fragrances'] })}
		{@render ListColumn({ title: 'Fashion', items: ['Clothes', 'Shoes', 'Jewelry'] })}
		{@render ListColumn({ title: 'Sports', items: ['Fitness', 'Outdoor', 'Team Sports'] })}
	</div>
{/snippet}

{#snippet OrdersContent()}
	{@render ActionCard([
		{ title: 'Track orders', desc: 'Real-time updates on packages', icon: Package },
		{ title: 'Order history', desc: 'Manage your past purchases', icon: Receipt },
		{ title: 'Returns & Exchanges', desc: 'Hassle-free within 30 days', icon: Exchange },
		{ title: 'My wishlist', desc: 'Items you saved for later', icon: Heart }
	])}
{/snippet}

{#snippet AccountContent()}
	{#if auth_state.is_authenticated}
		{@render ActionCard([
			{ title: 'Profile Info', desc: 'Manage your personal details', icon: User },
			{ title: 'Security', desc: 'Passwords and authentication', icon: ShieldLock },
			{ title: 'Payment Methods', desc: 'Cards and billing addresses', icon: CreditCard },
			{ title: 'Notifications', desc: 'Manage your alerts', icon: BellRinging }
		])}
	{:else}
		{@render ActionCard([
			{ title: 'Sign up', desc: 'Create an account', icon: UserPlus, href: '/account/signup' },
			{ title: 'Log in', desc: 'Access an existing account', icon: Login, href: '/account/login' }
		])}
	{/if}
{/snippet}

{#snippet SupportContent()}
	{@render ActionCard([
		{ title: 'Contact Us', desc: 'Get in touch with support', icon: Receipt },
		{ title: 'Privacy & Data Handling', desc: 'Read our policies', icon: Exchange },
		{ title: 'Return & Refund Policy', desc: 'Read our policies', icon: TruckDelivery },
		{ title: 'FAQ', desc: 'Find answers quickly', icon: Package },
		{ title: 'About Us', desc: 'Learn more about us', icon: Heart }
	])}
{/snippet}

<!-- ─── COMPONENT MARKUP ─── -->
<div
	class="relative flex items-center justify-center text-sm"
	onmouseleave={handleMouseLeave}
	role="menubar"
	tabindex="0"
	bind:this={navContainer}
>
	<!-- Sliding Pill Background -->
	{#if mounted && activePillId}
		<div
			in:fade={{ duration: 100, easing: expoOut }}
			out:fade={{ duration: 100, easing: quartIn }}
			class="pointer-events-none absolute top-1/2 left-0 z-0 h-10 -translate-y-1/2 rounded-full bg-nav-pill-bg transition-[transform,width] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
			style={pillStyle}
		></div>
	{/if}

	<!-- Links Container -->
	<div class="relative z-10 inline-flex">
		{#each links as link (link.label)}
			{@const isPillActive = activePillId === link.label}
			<div
				data-link-id={link.label}
				onmouseenter={() => handleMouseEnter(link)}
				role="presentation"
			>
				<a
					href={link.href ?? null}
					class={`
					${isPillActive ? 'font-semibold text-nav-pill-foreground' : 'text-nav-foreground'}
					flex h-10 cursor-pointer items-center
						justify-center
						px-4 transition-colors duration-300 `}
				>
					{link.label}
				</a>
			</div>
		{/each}
	</div>
</div>
