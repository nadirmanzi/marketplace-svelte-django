<script lang="ts">
	import MainNavigation from '$lib/components/navigation/main-navigation.svelte';

	let { children } = $props();
</script>

<main class="flex flex-col">
	<MainNavigation />

	<div class="flex-1 overflow-y-auto">
		{@render children?.()}
	</div>
</main>
