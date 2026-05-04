<script lang="ts">
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	const NAVIGATION = [
		{ name: 'Overview', href: '/ui' },
		{ name: 'Button', href: '/ui/button' },
		{ name: 'Input', href: '/ui/input' }
	];
</script>

<div class="flex min-h-screen w-screen bg-background p-2 text-foreground">
	<!-- Sidebar Navigation -->
	<aside class="w-[20rem] shrink-0 border-r border-foreground/10 bg-surface">
		<div class="sticky top-0 space-y-8 p-6 md:px-8 md:py-16">
			<div>
				<h2 class="mb-4 px-3 text-xs font-bold tracking-widest text-foreground/40 uppercase">
					Design System
				</h2>
				<nav class="space-y-1">
					{#each NAVIGATION as item}
						{@const isActive = $page.url.pathname === item.href}
						<a
							href={item.href}
							class="flex items-center rounded-xl px-3 py-2 text-sm font-medium transition-colors {isActive
								? 'bg-primary-tonal text-on-primary-tonal'
								: 'text-foreground/70 hover:bg-surface hover:text-foreground'}"
						>
							{item.name}
						</a>
					{/each}
				</nav>
			</div>
		</div>
	</aside>

	<!-- Main Content Area -->
	<main
		class="relative flex h-screen flex-1 flex-col items-center justify-start overflow-y-auto bg-background px-6 py-16"
	>
		<div class="w-full max-w-5xl">
			{@render children()}
		</div>
	</main>
</div>
