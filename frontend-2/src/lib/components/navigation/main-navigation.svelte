<script lang="ts">
	import MainNavLinks from './main-nav-links.svelte';
	import WhiteLogo from '$lib/assets/white-logo.svg';
	import BlackLogo from '$lib/assets/black-logo.svg';
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import ShoppingBag from '@tabler/icons-svelte-runes/icons/shopping-bag';
	import { fade, fly } from 'svelte/transition';

	let activeLink = $state<{
		label: string;
		href: string;
		content: string;
		render?: import('svelte').Snippet;
	} | null>(null);

	let isOpen = $state(false);
	let isClosing = $state(false);
	let isCrossHover = $state(false);

	// --- Height Animation Logic ---
	let contentElement = $state<HTMLElement | null>(null);
	let currentHeight = $state(0);

	$effect(() => {
		if (!contentElement) {
			currentHeight = 0;
			return;
		}
		const observer = new ResizeObserver((entries) => {
			for (let entry of entries) {
				currentHeight = entry.contentRect.height;
			}
		});
		observer.observe(contentElement);
		return () => observer.disconnect();
	});

	function handleHover(link: any) {
		// Cancel any in-progress close
		isClosing = false;

		// If the link does not have a render snippet (e.g., 'Support'), it acts like a mouse leave
		if (!link.render) {
			handleMouseLeave();
			return;
		}

		if (isOpen && activeLink && activeLink.label !== link.label) {
			isCrossHover = true;
		} else if (!isOpen) {
			isCrossHover = false;
		}
		activeLink = link;
		isOpen = true;
	}

	function handleMouseLeave() {
		isClosing = true;

		// After content has faded out (150ms), collapse the height
		setTimeout(() => {
			if (isClosing) {
				isOpen = false;
				isCrossHover = false;
			}
		}, 200);

		// After height has collapsed, clear activeLink
		setTimeout(() => {
			if (!isOpen) activeLink = null;
			isClosing = false;
		}, 550);
	}
</script>

<div class="fixed top-0 z-50 w-screen bg-white" onmouseleave={handleMouseLeave} role="navigation">
	<nav class="flex h-16 w-full items-center justify-center gap-16 p-1 px-8">
		<section onmouseenter={handleMouseLeave} role="presentation">
			<a href="/">
				<img src={WhiteLogo} alt="Logo" class="hidden size-8 dark:block" />
				<img src={BlackLogo} alt="Logo" class="size-8 dark:hidden" />
			</a>
		</section>
		<section>
			<MainNavLinks onHover={handleHover} {isCrossHover} activeLabel={activeLink?.label} />
		</section>
		<section
			class="flex items-center justify-center gap-6"
			onmouseenter={handleMouseLeave}
			role="presentation"
		>
			<Search class="size-6 cursor-pointer transition-colors hover:text-primary" stroke={1.5} />
			<ShoppingBag
				class="size-6 cursor-pointer transition-colors hover:text-primary"
				stroke={1.5}
			/>
		</section>
	</nav>

	<div
		class="overflow-hidden transition-[height] duration-300 ease-in-out"
		style="height: {isOpen ? currentHeight : 0}px; transition-delay: {isOpen ? '0ms' : '200ms'};"
	>
		<div bind:this={contentElement} class="w-full">
			{#if activeLink && (isOpen || isClosing)}
				<div class="py-10">
					<div class="mx-auto max-w-6xl">
						<div class="grid grid-cols-1 items-start">
							{#key activeLink.label}
								<div class="col-start-1 row-start-1 grid grid-cols-12 gap-10">
									<div class="col-span-3 border-r border-foreground/20 px-10">
										<h2
											class="text-2xl font-bold tracking-tight text-primary"
											in:fly={{
												x: isCrossHover ? -10 : 0,
												y: isCrossHover ? 0 : 15,
												duration: 250,
												delay: isCrossHover ? 150 : 50
											}}
											out:fly={{ x: 10, duration: 150 }}
										>
											{activeLink.label}
										</h2>
										<p
											class="mt-3 text-sm leading-relaxed text-foreground/50"
											in:fade={{ duration: 250, delay: isCrossHover ? 150 : 100 }}
											out:fade={{ duration: 150 }}
										>
											{activeLink.content}
										</p>
									</div>

									<div
										class="col-span-9"
										in:fade={{ duration: 250, delay: isCrossHover ? 150 : 150 }}
										out:fade={{ duration: 150 }}
									>
										{#if activeLink.render}
											{@render activeLink.render()}
										{/if}
									</div>
								</div>
							{/key}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.overflow-hidden {
		will-change: height;
	}
</style>
