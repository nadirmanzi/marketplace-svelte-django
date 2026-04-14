<script lang="ts">
	/*
	 * ─── SEARCH BAR ─────────────────────────────────────────────────────────────
	 * A localized search interface designed to be embedded within the main navigation.
	 * Utilizes a sliding drawer entry and is tightly integrated with the global Input.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import Input from '../ui/input.svelte';
	import { fly } from 'svelte/transition';
	import Button from '../ui/button.svelte';
	import X from '@tabler/icons-svelte-runes/icons/x';
	import { enhance } from '$app/forms';

	// ─── PROPS ───────────────────────────────────────────────────────────────────
	let {
		isOpen = $bindable() // Linked to Parent's `isSearchOpen` state
	}: {
		isOpen: boolean;
	} = $props();

	// ─── STATE ───────────────────────────────────────────────────────────────────
	let query = $state('');

	// ─── TRANSITIONS ─────────────────────────────────────────────────────────────
	/** Graceful In: Decelerates smoothly for a high-end drop-down effect */
	function gracefulIn(t: number): number {
		return 1 - Math.pow(1 - t, 4); // Quartic Out
	}

	/** Graceful Out: Accelerates moderately for a quick exit */
	function gracefulOut(t: number): number {
		return Math.pow(t, 3); // Cubic In
	}
</script>

<!-- Outer Search Context -->
<div class="flex items-center justify-center p-4">
	<!-- 
		Search Form Container 
		Note: in:fly|global ensures the search bar drops in from the nav bar 
		at the same time the drawer height expands.
	-->
	<form
		use:enhance
		class="w-full max-w-xl"
		in:fly|global={{ y: -20, delay: 200, duration: 400, easing: gracefulIn }}
		out:fly|global={{ y: -20, duration: 150, delay: 0, easing: gracefulOut }}
		method="POST"
	>
		<!-- 
			Integrated Input Component 
			Using 'dark' context to match the navigation background.
		-->
		<Input
			context="dark"
			size="lg"
			placeholder="Search products, categories, or brands..."
			autofocus={isOpen}
			// Programmatic focus on drawer entry
			bind:value={query}
		>
			{#snippet leading()}
				<Search stroke={2} class="size-6" />
			{/snippet}

			<!-- {#snippet trailing()}
				<Button
					onclick={() => {
						query = '';
					}}
					variant="filled"
					color="secondary"
					class="-mr-3"
					size="icon"
					type="submit"
				>
					<Search stroke={2} class="size-6" />
				</Button>
			{/snippet} -->
		</Input>
	</form>
</div>
