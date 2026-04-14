<script lang="ts">
	/*
	 * ─── ANIMATED PILL ITEM ────────────────────────────────────────────────────
	 * A child item designed to be used inside an `AnimatedPillGroup`.
	 * It automatically registers its DOM node with the parent group
	 * and communicates its hover/active status via Svelte Context.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import { getContext, onMount } from 'svelte';
	import { cn } from '$lib/utils';
	import type { Snippet } from 'svelte';

	// ─── TYPES ───────────────────────────────────────────────────────────────────
	interface Props {
		/** Unique identifier for this item (e.g. "search", "shop") */
		id: string;
		/** Forcefully toggle the group's "active" state to this item */
		active?: boolean;
		href?: string;
		children: Snippet;
		class?: string;
		/** CSS classes to apply when the pill is focused on this item */
		activeClass?: string;
		/** CSS classes to apply when the pill is elsewhere */
		inactiveClass?: string;
		// Standard mouse events
		onmouseenter?: (e: MouseEvent) => void;
		onmouseleave?: (e: MouseEvent) => void;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		id,
		active = false,
		href,
		children,
		class: className,
		activeClass = 'text-on-primary',
		inactiveClass = 'text-white',
		onmouseenter,
		onmouseleave,
		onclick
	}: Props = $props();

	// ─── STATE ───────────────────────────────────────────────────────────────────
	let element = $state<HTMLElement | null>(null);
	let isHovered = $state(false);

	// ─── CONTEXT ─────────────────────────────────────────────────────────────────
	/** Accesses the parent group's API for coordination */
	const group = getContext<{
		register: (id: string, el: HTMLElement) => () => void;
		setActive: (id: string | null) => void;
		activeId: () => string | null;
	}>('pill-group');

	// ─── SYNC LOGIC ────────────────────────────────────────────────────────────

	// Lifecycle: Register this node with the parent for measurement
	onMount(() => {
		if (element && group) {
			const unregister = group.register(id, element);
			return unregister;
		}
	});

	// Reactivity: Sync the 'active' prop and hover state with the parent's focal state
	$effect(() => {
		const currentActiveId = group?.activeId();

		if (isHovered) {
			// Hover always takes priority
			group?.setActive(id);
		} else if (active) {
			// If we are declaratively active, we take the highlight
			// ONLY if no other item is currently being hovered.
			if (currentActiveId === null || currentActiveId === id) {
				group?.setActive(id);
			}
		} else {
			// If we aren't hovered and aren't active, we clear the highlight
			// ONLY if we are the ones currently holding it.
			if (currentActiveId === id) {
				group?.setActive(null);
			}
		}
	});

	// ─── HANDLERS ───────────────────────────────────────────────────────────────
	function handleMouseEnter(e: MouseEvent) {
		isHovered = true;
		onmouseenter?.(e);
	}

	function handleMouseLeave(e: MouseEvent) {
		isHovered = false;
		onmouseleave?.(e);
	}
</script>

{#if href}
	<!-- Semantic Link variant -->
	<a
		bind:this={element}
		{href}
		class={cn(
			'block transition-colors duration-200',
			active ? activeClass : inactiveClass,
			className
		)}
		onmouseenter={handleMouseEnter}
		onmouseleave={handleMouseLeave}
		{onclick}
	>
		{@render children()}
	</a>
{:else}
	<!-- Standard Button variant -->
	<div
		bind:this={element}
		role="presentation"
		class={cn(
			'flex cursor-pointer items-center justify-start space-x-2 px-2 transition-colors duration-200',
			active ? activeClass : inactiveClass,
			className
		)}
		onmouseenter={handleMouseEnter}
		onmouseleave={handleMouseLeave}
		{onclick}
	>
		{@render children()}
	</div>
{/if}
