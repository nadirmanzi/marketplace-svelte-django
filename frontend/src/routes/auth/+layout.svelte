<script lang="ts">
	import { onNavigate } from '$app/navigation';
	import { page } from '$app/state';
	import Logo from '$lib/components/logo.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import ArrowLeft from '@tabler/icons-svelte-runes/icons/arrow-left';

	const { children } = $props();
	const is_login = $derived(page.url.pathname === '/auth/login');
	const is_signup = $derived(page.url.pathname === '/auth/signup');

	onNavigate((navigation) => {
		if (!document.startViewTransition) return;

		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});
</script>

<div class="h-full w-full">
	<nav class="absolute top-0 left-0 z-50 flex h-20 w-full items-center justify-between px-10">
		<Button
			size="md"
			color="secondary"
			variant="ghost"
			class={is_login ? 'bg-foreground text-white' : 'bg-surface text-foreground'}
			onclick={() => {
				history.back();
			}}
			><ArrowLeft />
			<p>Back</p></Button
		>
		<a href="/">
			<Logo class="size-10" color={is_login ? 'white' : 'black'} />
		</a>
	</nav>
	{@render children?.()}
</div>

<style>
	:root {
		view-transition-name: auth-layout;
	}

	::view-transition-old(root) {
		animation: 100ms ease-in both fade-out;
	}

	::view-transition-new(root) {
		animation: 100ms ease-out both fade-in;
	}

	@keyframes fade-out {
		from {
			opacity: 1;
		}
		to {
			opacity: 0;
		}
	}

	@keyframes fade-in {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
</style>
