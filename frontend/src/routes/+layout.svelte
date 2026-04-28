<script lang="ts">
	import { auth_state, setAuth, revokeAuth } from '$lib/client/state/auth.svelte';
	import '../app.css';
	import favicon from '$lib/assets/white-logo.svg';

	let { data, children } = $props();

	$effect(() => {
		if (data.is_authenticated && data.user) {
			setAuth(data.user);
		} else {
			revokeAuth();
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Marketplace</title>
</svelte:head>

<main class="h-dvh w-screen bg-background text-foreground">
	{@render children()}
</main>
