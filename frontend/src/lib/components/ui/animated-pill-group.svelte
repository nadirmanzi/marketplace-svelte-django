<script lang="ts">
	/*
	 * ─── ANIMATED PILL GROUP ───────────────────────────────────────────────────
	 * A sophisticated layout container that manages a single "sliding pill"
	 * background shared across multiple child items.
	 * Uses Svelte Context and ResizeObserver for high-precision, performant physics.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import { setContext } from 'svelte';
	import { SvelteMap } from 'svelte/reactivity';

	let { color = 'bg-nav-hover', pillClass = 'rounded-full', children } = $props();

	// ─── STATE ───────────────────────────────────────────────────────────────────
	let mounted = $state(false);
	let activeId = $state<string | null>(null);
	let container = $state<HTMLElement | null>(null);

	// Physics State: Preserving these prevents the "jump from (0,0)" bug
	let pillWidth = $state(0);
	let pillHeight = $state(0);
	let pillTransform = $state('translate3d(0,0,0)');
	let isVisible = $state(false);

	// ─── REFS / REGISTRY ─────────────────────────────────────────────────────────
	const items = new SvelteMap<string, HTMLElement>();

	let isGroupHovered = $state(false);

	// ─── CONTEXT ─────────────────────────────────────────────────────────────────
	setContext('pill-group', {
		register: (id: string, el: HTMLElement) => {
			items.set(id, el);
			return () => items.delete(id);
		},
		setActive: (id: string | null) => {
			if (id) {
				activeId = id;
			} else if (!isGroupHovered) {
				// Only clear if the user has left the entire group area
				activeId = null;
			}
		},
		activeId: () => activeId
	});

	// ─── MEASUREMENT & PHYSICS ──────────────────────────────────────────────────

	/** Performs calculated repositioning of the pill to match target element bounds */
	function updatePill() {
		if (!container) return;

		if (!activeId) {
			isVisible = false;
			return;
		}

		const activeEl = items.get(activeId);
		if (activeEl) {
			const rect = activeEl.getBoundingClientRect();
			const containerRect = container.getBoundingClientRect();

			pillWidth = rect.width;
			pillHeight = rect.height;
			pillTransform = `translate3d(${rect.left - containerRect.left}px, ${rect.top - containerRect.top}px, 0)`;
			isVisible = true;
		}
	}

	// ─── EFFECTS ────────────────────────────────────────────────────────────────
	$effect(() => {
		mounted = true;
		if (!container) return;

		// React to the parent container's size changes (e.g. Navigation drawer expansion)
		const observer = new ResizeObserver(updatePill);
		observer.observe(container);
		return () => observer.disconnect();
	});

	// Re-run pill logic whenever the active focus shifts
	$effect(updatePill);
</script>

<div
	bind:this={container}
	class="relative flex h-full items-center justify-center"
	onmouseenter={() => (isGroupHovered = true)}
	onmouseleave={() => {
		isGroupHovered = false;
		activeId = null;
	}}
	role="presentation"
>
	<!-- 
		The Sliding Pill 
		Uses hardware-accelerated translations and custom bezier curves 
		to maximize the "wow" factor during rapid movement.
	-->
	{#if mounted}
		<div
			class="pointer-events-none absolute top-0 left-0 z-0 transition-[transform,width,height,opacity] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] {color} {pillClass}"
			style="
				width: {pillWidth}px;
				height: {pillHeight}px;
				transform: {pillTransform};
				opacity: {isVisible ? 1 : 0};
			"
		></div>
	{/if}

	<!-- Link List / Children -->
	<div class="relative z-10 flex h-full w-full">
		{@render children()}
	</div>
</div>
