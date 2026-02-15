<script lang="ts">
	let { children } = $props();
	import AuthNavigation from '$lib/components/navigation/auth-navigation.svelte';
</script>

<div class="flex h-dvh w-full flex-col">
	<AuthNavigation />
	<div class="flex h-[calc(100dvh-4rem)] w-full flex-1 bg-red-300">
		{@render children?.()}
	</div>
</div>
