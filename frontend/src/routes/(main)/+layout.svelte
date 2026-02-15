<script lang="ts">
	import { onNavigate } from '$app/navigation';
	import MainNavigation from '$lib/components/navigation/main-navigation.svelte';
	import Button from '$lib/components/ui/button/button.svelte';

	let { children } = $props();

	const links = [
		{ href: '/', label: 'Home' },
		{ href: '/browse', label: 'Browse' },
		{ href: '/categories', label: 'Categories' }
	];

	$effect(() => {
		onNavigate((navigation) => {
			if (!document.startViewTransition) return;

			// Determine direction: if delta is negative, it's a "back" nav
			const isBack = (navigation.delta ?? 0) < 0;
			document.documentElement.classList.toggle('back-transition', isBack);

			return new Promise((resolve) => {
				document.startViewTransition(async () => {
					resolve();
					await navigation.complete;
				});
			});
		});
	});
</script>

<MainNavigation {links}>
	<svelte:fragment slot="actions">
		<Button variant="ghost">Sign up</Button>
		<Button>Log in</Button>
	</svelte:fragment>
</MainNavigation>
<main class="flex min-h-dvh w-full flex-1 flex-col overflow-x-hidden overflow-y-auto bg-background">
	{@render children()}
</main>

<style>
	main {
		view-transition-name: main-content;
	}

	@keyframes fade-in {
		from {
			opacity: 0;
		}
	}
	@keyframes fade-out {
		to {
			opacity: 0;
		}
	}

	@keyframes slide-from-right {
		from {
			transform: translateX(100px);
		}
	}

	@keyframes slide-to-left {
		to {
			transform: translateX(-100px);
		}
	}

	@keyframes slide-to-right {
		to {
			transform: translateX(100px);
		}
	}
	@keyframes slide-from-left {
		from {
			transform: translateX(-100px);
		}
	}

	/* Standard Transitions (Forward) */
	:root::view-transition-old(main-content) {
		animation:
			90ms cubic-bezier(0.4, 0, 1, 1) both fade-out,
			300ms cubic-bezier(0.4, 0, 0.2, 1) both slide-to-left;
	}
	:root::view-transition-new(main-content) {
		animation:
			210ms cubic-bezier(0, 0, 0.2, 1) 90ms both fade-in,
			300ms cubic-bezier(0.4, 0, 0.2, 1) both slide-from-right;
	}

	/* 4. Back Transitions (Reverse) */
	:root.back-transition::view-transition-old(main-content) {
		animation:
			90ms cubic-bezier(0.4, 0, 1, 1) both fade-out,
			300ms cubic-bezier(0.4, 0, 0.2, 1) both slide-to-right;
	}
	:root.back-transition::view-transition-new(main-content) {
		animation:
			210ms cubic-bezier(0, 0, 0.2, 1) 90ms both fade-in,
			300ms cubic-bezier(0.4, 0, 0.2, 1) both slide-from-left;
	}

	/* 5. Accessibility: Respect user preference */
	@media (prefers-reduced-motion: reduce) {
		::view-transition-group(*),
		::view-transition-old(*),
		::view-transition-new(*) {
			animation: none !important;
		}
	}
</style>
