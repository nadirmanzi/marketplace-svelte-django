<script lang="ts">
	import MainNavigation from '$lib/components/main-navigation.svelte';

	let { children } = $props();
</script>

<MainNavigation />
<!-- <div class="bg-[url('/hero1.jpg')] bg-center bg-no-repeat bg-cover h-dvh"></div> -->
<div class="">{@render children?.()}</div>


