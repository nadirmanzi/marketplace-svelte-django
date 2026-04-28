<script lang="ts">
	/*
	 * ─── MAIN NAVIGATION ─────────────────────────────────────────────────────────
	 * The architectural core of the navigation system.
	 * Manages the top bar, the mega-menu expansion, and the search overlay state.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */

	import MainNavLinks from './main-nav-links.svelte';
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import ShoppingBag from '@tabler/icons-svelte-runes/icons/shopping-bag';
	import AnimatedPillGroup from '$lib/components/ui/animated-pill-group.svelte';
	import AnimatedPillItem from '$lib/components/ui/animated-pill-item.svelte';
	import { fade } from 'svelte/transition';
	import type { Snippet } from 'svelte';
	import SearchBar from './search-bar.svelte';
	import Sheet from '$lib/components/ui/sheet.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Logo from '../logo.svelte';

	// ─── ANIMATION CONSTANTS ─────────────────────────────────────────────────────
	// Linear-to-curved easing for a "premium" feel.

	/** Graceful In: Starts quite fast, decelerates very smoothly over a long tail */
	function gracefulIn(t: number): number {
		return 1 - Math.pow(1 - t, 4); // Quartic Out
	}

	/** Graceful Out: Starts slowly, accelerates moderately */
	function gracefulOut(t: number): number {
		return Math.pow(t, 3); // Cubic In
	}

	// ─── NAVIGATION STATE ───────────────────────────────────────────────────────
	interface NavLink {
		label: string;
		description: string;
		href?: string;
		render?: Snippet;
	}

	let navElement = $state<HTMLElement | null>(null);
	let activeLink = $state<NavLink | null>(null);
	let isOpen = $state(false); // Controls mega-menu visibility
	let isClosing = $state(false); // Tracks outgoing animation phase
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	let isCrossHover = $state(false); // Tracks if moving between links
	let isSearchOpen = $state(false); // Controls search overlay
	let isCartOpen = $state(false); // Controls shopping cart sheet
	let isUserMenuOpen = $state(false); // Controls auth dropdown state

	// ─── HEIGHT ANIMATION LOGIC ──────────────────────────────────────────────────

	// Dynamically measures the content container to animate the nav drawer's height.
	let contentElement = $state<HTMLElement | null>(null);
	let currentHeight = $state(0);
	let hoverTimeout: ReturnType<typeof setTimeout>;

	$effect(() => {
		if (!contentElement) {
			currentHeight = 0;
			return;
		}
		// ResizeObserver allows us to react to content height changes (even if images load late)
		const observer = new ResizeObserver((entries) => {
			for (let entry of entries) {
				currentHeight = entry.contentRect.height;
			}
		});
		observer.observe(contentElement);
		return () => observer.disconnect();
	});

	// ─── GLOBAL EVENT HANDLERS ──────────────────────────────────────────────────

	/** Closes active menus when clicking anywhere outside the navigation boundary */
	function handleGlobalClick(e: MouseEvent) {
		if (isOpen || isSearchOpen || isUserMenuOpen) {
			const target = e.target as Node;
			// If target was removed from DOM (like a cleared button), ignore outside click logic
			if (!document.contains(target)) return;

			if (navElement && !navElement.contains(target)) {
				isOpen = false;
				isSearchOpen = false;
				isCartOpen = false;
				isUserMenuOpen = false;
				activeLink = null;
			}
		}
	}

	/** Broadly catch any clicks occurring inside the navigation (e.g. Navigating away) */
	function handleNavClick(e: MouseEvent) {
		const target = e.target as HTMLElement;
		// If an Anchor tag was clicked, forcefully slam everything closed for a clean page transition
		if (target.closest('a')) {
			isOpen = false;
			isSearchOpen = false;
			isCartOpen = false;
			isUserMenuOpen = false;
			activeLink = null;
			isClosing = false;
		}
	}

	// ─── HOVER/CONTEXT LOGIC ────────────────────────────────────────────────────

	/** Triggered when hovering a main navigation link */
	function handleHover(link: NavLink) {
		isClosing = false;
		clearTimeout(hoverTimeout);

		if (isSearchOpen) {
			isSearchOpen = false;
			// Sequential transition: let search fly out before opening the mega menu
			hoverTimeout = setTimeout(() => {
				openMegaMenu(link);
			}, 250);
		} else {
			openMegaMenu(link);
		}
	}

	/** Toggles the Search Interface */
	function handleSearchToggle() {
		clearTimeout(hoverTimeout);

		if (isSearchOpen) {
			isSearchOpen = false;
		} else {
			if (isOpen) {
				isOpen = false;
				activeLink = null;
				isUserMenuOpen = false;
				// Smooth transition from mega-menu to search
				hoverTimeout = setTimeout(() => {
					isSearchOpen = true;
				}, 250);
			} else {
				isSearchOpen = true;
				isUserMenuOpen = false;
			}
		}
	}

	/** Opens the mega-menu drawer with the specified link's content */
	function openMegaMenu(link: NavLink) {
		if (!link.render) {
			handleMouseLeave();
			return;
		}

		// Detect if we are switching between links while already open
		if (isOpen && activeLink && activeLink.label !== link.label) {
			isCrossHover = true;
		} else if (!isOpen) {
			isCrossHover = false;
		}

		activeLink = link;
		isOpen = true;
	}

	/** Triggered when the mouse leaves the entire nav or enters an "Action Area" (Logo, Cart) */
	function handleMouseLeave() {
		isClosing = true;
		isSearchOpen = false; // Search bar closes when leaving the nav boundary
		clearTimeout(hoverTimeout);

		// Stage 1: Collapse height after a short grace period (if no other link is hovered)
		setTimeout(() => {
			if (isClosing) {
				isOpen = false;
			}
		}, 10);

		// Stage 2: Reset everything after the Drawer height has fully collapsed
		setTimeout(() => {
			if (!isOpen) {
				activeLink = null;
				isClosing = false;
			}
		}, 500); // 500ms matches the height transition duration
	}

	/** Toggles the Shopping Cart Sheet and closes other active views */
	function handleCartClick() {
		// Close mega-menu, search, and user menu before opening the sheet
		isOpen = false;
		isSearchOpen = false;
		isUserMenuOpen = false;
		activeLink = null;

		isCartOpen = !isCartOpen;
	}
</script>

<svelte:window onclick={handleGlobalClick} />

<!-- 
	Main Navigation Outer Boundary 
	Positioned fixed at the top. onmouseleave ensures collapse on exit.
-->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div
	bind:this={navElement}
	class="fixed top-0 z-50 w-full border-b border-nav-border bg-nav-bg backdrop-blur-3xl"
	onmouseleave={handleMouseLeave}
	onclick={handleNavClick}
	role="navigation"
>
	<!-- Top Bar Container -->
	<nav class="flex h-20 w-full items-center justify-center gap-30 px-8">
		<!-- Branding / Logo -->
		<a href="/ui">
			<Logo color="white" class="size-10" />
		</a>

		<!-- Central Navigation Links -->
		<section>
			<MainNavLinks onHover={handleHover} activeLinkLabel={activeLink?.label} {isOpen} />
		</section>

		<!-- Right Side Actions -->
		<section class="flex items-center justify-center" role="presentation">
			<AnimatedPillGroup color="bg-nav-bg-hover">
				<!-- Search Integration: Opens on hover, closes on nav leave or category hover -->
				<AnimatedPillItem
					id="search"
					active={isSearchOpen}
					class="size-10 text-nav-foreground [&_svg]:size-5"
					onclick={handleSearchToggle}
				>
					<Search stroke={1.5} />
				</AnimatedPillItem>

				<AnimatedPillItem
					id="cart"
					class="size-10 text-nav-foreground [&_svg]:size-5"
					onclick={handleCartClick}
				>
					<ShoppingBag stroke={1.5} />
				</AnimatedPillItem>
			</AnimatedPillGroup>
		</section>
	</nav>

	<!-- 
		Mega-Menu Drawer 
		Smoothly transitions height and contains either Link content or Search.
	-->
	<div
		class="overflow-hidden border-t-[1.5px] border-white/5 shadow-none transition-[height] duration-500 {isOpen ||
		isSearchOpen
			? ' ease-[cubic-bezier(0.16,1,0.3,1)]'
			: ' ease-[cubic-bezier(0.7,0,0.84,0)]'}"
		style="height: {isOpen || isSearchOpen ? currentHeight : 0}px; transition-delay: {isOpen ||
		isSearchOpen
			? '100ms'
			: '100ms'}; transition-duration: {isOpen || isSearchOpen ? '1000ms' : '500ms'};"
	>
		<div bind:this={contentElement} class="w-full">
			<!-- Navigation Category Content -->
			{#if activeLink && (isOpen || isClosing) && !isSearchOpen}
				<div class="grid grid-cols-1 grid-rows-1">
					{#key activeLink.label}
						<div class="col-start-1 row-start-1 px-12 pt-12 pb-20">
							<div class="mx-auto max-w-7xl">
								<div class="grid grid-cols-12 gap-16">
									<!-- Pillar 1: Context & Meta (30%) -->
									<div
										class="col-span-4 space-y-4"
										in:fade|global={{
											duration: 200,
											delay: 200,
											easing: gracefulIn
										}}
										out:fade|global={{
											duration: 200,
											easing: gracefulOut
										}}
									>
										<h2 class="font-display text-2xl font-bold tracking-tight text-white">
											{activeLink.label}
										</h2>
										<p class="max-w-xs text-sm leading-relaxed text-nav-foreground-muted">
											{activeLink.description}
										</p>
									</div>

									<!-- Pillar 2: Dynamic Content (70%) -->
									<div class="col-span-8 border-l border-nav-border pl-16">
										{#if activeLink.render}
											<div
												in:fade|global={{
													duration: 200,
													delay: 200,
													easing: gracefulIn
												}}
												out:fade|global={{
													duration: 200,
													easing: gracefulOut
												}}
												class=""
											>
												{@render activeLink.render()}
											</div>
										{/if}
									</div>
								</div>
							</div>
						</div>
					{/key}
				</div>
			{/if}

			<!-- Universal Search Interface -->
			{#if isSearchOpen}
				<div class="py-4">
					<SearchBar bind:isOpen={isSearchOpen} />
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- 
	Shopping Cart Sheet 
	Slide-over from the right for cart management.
	Moved outside the sticky boundary to ensure z-index priority.
-->
<Sheet bind:open={isCartOpen}>
	{#snippet header()}
		<div class="">
			<h3 class="text-lg font-bold text-foreground">Shopping Bag</h3>
		</div>
	{/snippet}

	{#snippet body()}
		<!-- Temporary Empty State -->
		<div class="mt-20 flex flex-col items-center justify-center gap-4 text-center">
			<div
				class="flex size-16 items-center justify-center rounded-full bg-foreground/5 text-foreground/30"
			>
				<ShoppingBag class="size-8" stroke={1} />
			</div>
			<div class="flex flex-col gap-1">
				<p class="font-medium text-foreground">Your bag is empty</p>
				<p class="text-sm text-foreground/50">Looks like you haven't added anything yet.</p>
			</div>
			<Button variant="outline" size="md" class="mt-4" onclick={() => (isCartOpen = false)}>
				Continue Shopping
			</Button>
		</div>
	{/snippet}

	{#snippet footer()}
		<div class="flex flex-col gap-4">
			<div class="flex items-center justify-between">
				<span class="text-sm text-foreground/60">Subtotal</span>
				<span class="text-base font-bold text-foreground">$0.00</span>
			</div>
			<!-- Primary Action Call to Action -->
			<Button class="w-full" size="lg" variant="filled" color="primary">Proceed to Checkout</Button>
		</div>
	{/snippet}
</Sheet>

<style>
	.overflow-hidden {
		will-change: height;
	}
</style>
