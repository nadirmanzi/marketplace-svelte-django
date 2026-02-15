<script lang="ts">
	import Logo from '$lib/components/logo.svelte';
	import type { Snippet } from 'svelte';

	let { children } = $props();
</script>

<nav class="@container fixed top-0 left-0 z-50 flex h-16 w-screen items-center justify-center">
	<div
		class="flex h-14 w-fit items-center justify-center space-x-16 rounded-full border border-nav-border bg-nav-background px-8 shadow-xs shadow-black/10"
	>
		<Logo />
		{@render children()}
	</div>
</nav>

<style>
	nav {
		view-transition-name: top-navigation;
	}
</style>
