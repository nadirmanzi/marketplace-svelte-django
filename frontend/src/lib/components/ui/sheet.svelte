<script lang="ts">
	/*
	 * ─── SHEET COMPONENT (SHARED UI) ─────────────────────────────────────────────
	 * A premium slide-over component that provides a contextual sidebar.
	 * Features include:
	 *  - Soft-blur backdrop (no darkening).
	 *  - Sticky Header & Footer with scrollable Body area.
	 *  - Global scroll lock on open.
	 *  - Responsive: Full width on mobile, 1/3 on desktop.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import { fly, fade } from 'svelte/transition';
	import { expoOut } from 'svelte/easing';
	import type { Snippet } from 'svelte';
	import X from '@tabler/icons-svelte-runes/icons/x';
	import Button from './button.svelte';

	interface Props {
		/** State control: bind to a boolean */
		open: boolean;
		/** Position to slide from */
		side?: 'left' | 'right';
		/** Persistent Header area (non-scrolling) */
		header?: Snippet;
		/** Main scrollable content area */
		body?: Snippet;
		/** Persistent Footer area (non-scrolling) */
		footer?: Snippet;
		/** Optional callback for closure */
		onClose?: () => void;
	}

	let { open = $bindable(), side = 'right', header, body, footer, onClose }: Props = $props();

	// ─── SCROLL LOCK LOGIC ───────────────────────────────────────────────────────
	$effect(() => {
		if (open) {
			const scrollBarWidth = window.innerWidth - document.documentElement.clientWidth;
			document.body.style.overflow = 'hidden';
			document.body.style.paddingRight = `${scrollBarWidth}px`;
		} else {
			document.body.style.overflow = '';
			document.body.style.paddingRight = '';
		}

		return () => {
			document.body.style.overflow = '';
			document.body.style.paddingRight = '';
		};
	});

	// ─── HANDLERS ───────────────────────────────────────────────────────────────
	function handleClose() {
		open = false;
		onClose?.();
	}

	/** Closes on Escape key press */
	function handleKeyboard(e: KeyboardEvent) {
		if (e.key === 'Escape') handleClose();
	}
</script>

<svelte:window onkeydown={handleKeyboard} />

<!-- 
	Container 
	We use fixed positioning to overlay everything on the page.
-->
{#if open}
	<div class="fixed inset-0 z-[999] flex">
		<!-- 
			Backdrop Overlay 
			Soft blur, minimal darkening for a modern, glass-like transition.
		-->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 bg-foreground/20 backdrop-blur-md"
			transition:fade={{ duration: 300, easing: expoOut }}
			onclick={handleClose}
		></div>

		<!-- 
			Sheet Content 
			Slides in from the side. Full height, responsive width.
		-->
		<div
			class={`
				relative flex h-dvh min-w-1/3 flex-col bg-surface transition-all
				${side === 'right' ? 'ml-auto' : 'mr-auto'}
			`}
			in:fly={{ x: side === 'right' ? 500 : -500, duration: 600, easing: expoOut }}
			out:fly={{ x: side === 'right' ? 500 : -500, duration: 400, easing: expoOut }}
		>
			<!-- 
				Sticky Header 
				Persistent top area with the close action.
			-->
			<header class="flex h-20 shrink-0 items-center border-b border-foreground/5 px-8">
				<div class="flex w-full items-center justify-between gap-4">
					{#if header}
						<div class="flex items-center text-xl font-bold tracking-tight">
							{@render header()}
						</div>
					{:else}
						<div class="flex items-center text-xl font-bold tracking-tight">Menu</div>
					{/if}

					<button
						onclick={handleClose}
						class="flex size-10 items-center justify-center rounded-full bg-background transition-colors hover:bg-foreground/10"
						aria-label="Close sheet"
					>
						<X stroke={2} class="size-6" />
					</button>
				</div>
			</header>

			<!-- 
				Scrollable Body 
				The only area that scrolls if content overflows.
			-->
			<main class="flex-1 overflow-y-auto px-8 py-6">
				{#if body}
					{@render body()}
				{/if}
			</main>

			<!-- 
				Sticky Footer 
				Persistent bottom area for primary actions (like Checkout).
			-->
			{#if footer}
				<footer
					class="shrink-0 border-t border-foreground/5 bg-background/50 px-8 py-6 backdrop-blur-xl"
				>
					{@render footer()}
				</footer>
			{/if}
		</div>
	</div>
{/if}
