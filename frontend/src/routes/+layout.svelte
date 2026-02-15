<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/primary-logo.svg';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
<div class="bg-background text-foreground">
	{@render children()}
</div>
