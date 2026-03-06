<script lang="ts">
	import MainNavigation from '$lib/components/navigation/main-navigation.svelte';

	let { children } = $props();
</script>

<main class="flex flex-col">
	<MainNavigation />

	<div class="">
		{@render children()}
	</div>
</main>
