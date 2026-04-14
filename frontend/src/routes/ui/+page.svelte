<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Home2 from '@tabler/icons-svelte-runes/icons/home-2';
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import ShoppingBag from '@tabler/icons-svelte-runes/icons/shopping-bag';
	import Heart from '@tabler/icons-svelte-runes/icons/heart';
	import Trash from '@tabler/icons-svelte-runes/icons/trash';
	import Check from '@tabler/icons-svelte-runes/icons/check';
	import Plus from '@tabler/icons-svelte-runes/icons/plus';
	import ArrowRight from '@tabler/icons-svelte-runes/icons/arrow-right';
	import Settings from '@tabler/icons-svelte-runes/icons/settings';
	import Download from '@tabler/icons-svelte-runes/icons/download';
	import Mail from '@tabler/icons-svelte-runes/icons/mail';
	import Eye from '@tabler/icons-svelte-runes/icons/eye';
	import EyeOff from '@tabler/icons-svelte-runes/icons/eye-off';
	import User from '@tabler/icons-svelte-runes/icons/user';
	import X from '@tabler/icons-svelte-runes/icons/x';

	let showPassword = $state(false);
	let searchValue = $state('');

	const colors = ['primary', 'secondary', 'destructive', 'success'] as const;
	const variants = ['filled', 'tonal', 'outline', 'ghost'] as const;
	const sizes = ['sm', 'md', 'lg'] as const;

	const colorTokens = [
		{
			group: 'Primary — Electric Blue',
			tokens: [
				{ name: '--color-primary', bg: 'bg-primary', fg: 'text-on-primary', label: 'primary' },
				{
					name: '--color-primary-hover',
					bg: 'bg-primary-hover',
					fg: 'text-on-primary',
					label: 'primary-hover'
				},
				{
					name: '--color-primary-tonal',
					bg: 'bg-primary-tonal',
					fg: 'text-on-primary-tonal',
					label: 'primary-tonal'
				},
				{
					name: '--color-primary-tonal-hover',
					bg: 'bg-primary-tonal-hover',
					fg: 'text-on-primary-tonal',
					label: 'primary-tonal-hover'
				}
			]
		},
		{
			group: 'Secondary — Vivid Orange',
			tokens: [
				{
					name: '--color-secondary',
					bg: 'bg-secondary',
					fg: 'text-on-secondary',
					label: 'secondary'
				},
				{
					name: '--color-secondary-hover',
					bg: 'bg-secondary-hover',
					fg: 'text-on-secondary',
					label: 'secondary-hover'
				},
				{
					name: '--color-secondary-tonal',
					bg: 'bg-secondary-tonal',
					fg: 'text-on-secondary-tonal',
					label: 'secondary-tonal'
				},
				{
					name: '--color-secondary-tonal-hover',
					bg: 'bg-secondary-tonal-hover',
					fg: 'text-on-secondary-tonal',
					label: 'secondary-tonal-hover'
				}
			]
		},
		{
			group: 'Destructive',
			tokens: [
				{
					name: '--color-destructive',
					bg: 'bg-destructive',
					fg: 'text-on-destructive',
					label: 'destructive'
				},
				{
					name: '--color-destructive-hover',
					bg: 'bg-destructive-hover',
					fg: 'text-on-destructive',
					label: 'destructive-hover'
				},
				{
					name: '--color-destructive-tonal',
					bg: 'bg-destructive-tonal',
					fg: 'text-on-destructive-tonal',
					label: 'destructive-tonal'
				},
				{
					name: '--color-destructive-tonal-hover',
					bg: 'bg-destructive-tonal-hover',
					fg: 'text-on-destructive-tonal',
					label: 'destructive-tonal-hover'
				}
			]
		},
		{
			group: 'Success',
			tokens: [
				{ name: '--color-success', bg: 'bg-success', fg: 'text-on-success', label: 'success' },
				{
					name: '--color-success-hover',
					bg: 'bg-success-hover',
					fg: 'text-on-success',
					label: 'success-hover'
				},
				{
					name: '--color-success-tonal',
					bg: 'bg-success-tonal',
					fg: 'text-on-success-tonal',
					label: 'success-tonal'
				},
				{
					name: '--color-success-tonal-hover',
					bg: 'bg-success-tonal-hover',
					fg: 'text-on-success-tonal',
					label: 'success-tonal-hover'
				}
			]
		},
		{
			group: 'Surfaces',
			tokens: [
				{
					name: '--color-background',
					bg: 'bg-background',
					fg: 'text-foreground',
					label: 'background'
				},
				{
					name: '--color-background-hover',
					bg: 'bg-background-hover',
					fg: 'text-foreground',
					label: 'background-hover'
				},
				{
					name: '--color-foreground',
					bg: 'bg-foreground',
					fg: 'text-background',
					label: 'foreground'
				},
				{ name: '--color-surface', bg: 'bg-surface', fg: 'text-on-surface', label: 'surface' },
				{
					name: '--color-surface-hover',
					bg: 'bg-surface-hover',
					fg: 'text-on-surface',
					label: 'surface-hover'
				}
			]
		}
	];
</script>

<svelte:head>
	<title>Design System — UI Showcase</title>
</svelte:head>

<div class="space-y-24">
	<!-- ─── HEADER ─── -->
	<header class="space-y-4 text-center">
		<div
			class="inline-flex items-center justify-center rounded-full bg-primary-tonal px-4 py-1.5 text-sm font-semibold tracking-wide text-on-primary-tonal"
		>
			Design System
		</div>
		<h1 class="text-4xl font-bold tracking-tight sm:text-5xl">Theme Showcase</h1>
		<p class="mx-auto max-w-2xl text-base text-foreground/60">
			A comprehensive visual reference for the soft sage green and muted rose color palette, surface
			interactions, and exhaustive button combinations.
		</p>
	</header>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Theme In Action                    -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-8" id="theme-in-action">
		<div class="space-y-2 text-center">
			<h2 class="text-2xl font-bold tracking-tight">Theme in Action</h2>
			<p class="text-sm text-foreground/60">
				A creative composition demonstrating how backgrounds, surfaces, text, and tonal button
				layers interact organically.
			</p>
		</div>

		<!-- Mock UI Composition -->
		<div class="overflow-hidden shadow-2xl ring-1 ring-foreground/5 sm:rounded-[2.5rem]">
			<div class="bg-background px-6 pt-12 pb-16 sm:px-12">
				<div class="relative mx-auto max-w-4xl space-y-8">
					<!-- Mock Header -->
					<div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
						<div class="space-y-1">
							<h3 class="text-2xl font-bold text-foreground">Marketing Campaign</h3>
							<p class="text-sm font-medium text-foreground/50">
								Manage your seasonal assets and analytics.
							</p>
						</div>
						<div class="flex gap-3">
							<Button variant="outline" color="secondary">
								<Settings /> Manage
							</Button>
							<Button color="primary" variant="filled">
								<Plus /> Create Campaign
							</Button>
						</div>
					</div>

					<!-- Mock Grid Cards -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
						<!-- Surface Card 1 -->
						<div
							class="space-y-6 rounded-4xl bg-surface p-8 shadow-sm ring-1 ring-surface-hover/50 transition-transform duration-300 hover:-translate-y-1"
						>
							<div class="flex items-start justify-between">
								<div
									class="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-tonal text-on-primary-tonal"
								>
									<Check class="size-6" />
								</div>
								<span
									class="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-xs font-bold text-success"
								>
									+12.5%
								</span>
							</div>
							<div>
								<p class="text-4xl font-extrabold tracking-tight">24.5k</p>
								<p class="mt-1 text-sm font-medium text-foreground/50">Active Conversions</p>
							</div>
						</div>

						<!-- Surface Card 2 -->
						<div
							class="space-y-6 rounded-4xl bg-surface p-8 shadow-sm ring-1 ring-surface-hover/50 transition-transform duration-300 hover:-translate-y-1"
						>
							<div class="flex items-start justify-between">
								<div
									class="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary-tonal text-on-secondary-tonal"
								>
									<Heart class="size-6" />
								</div>
								<span
									class="inline-flex items-center gap-1 rounded-full bg-foreground/5 px-2.5 py-1 text-xs font-bold text-foreground/70"
								>
									Trending
								</span>
							</div>
							<div>
								<p class="text-4xl font-extrabold tracking-tight">Rose</p>
								<p class="mt-1 text-sm font-medium text-foreground/50">Top Accent Color</p>
							</div>
						</div>

						<!-- High Contrast Dark Card -->
						<div
							class="relative overflow-hidden rounded-4xl bg-foreground p-8 text-background shadow-xl transition-transform duration-300 hover:-translate-y-1"
						>
							<div
								class="absolute -top-8 -right-8 h-32 w-32 rounded-full bg-primary/30 blur-3xl"
							></div>
							<div
								class="absolute -bottom-12 -left-12 h-40 w-40 rounded-full bg-secondary/20 blur-3xl"
							></div>

							<div class="relative z-10 flex h-full flex-col justify-between space-y-8">
								<div class="space-y-2">
									<p class="text-sm font-semibold tracking-wide text-background/60 uppercase">
										Pro Analytics
									</p>
									<p class="text-2xl leading-tight font-bold">Unlock deep audience insights.</p>
								</div>
								<Button
									class="w-full bg-background text-foreground hover:bg-background-hover focus-visible:ring-background"
								>
									Upgrade Now <ArrowRight />
								</Button>
							</div>
						</div>
					</div>

					<!-- List Section -->
					<div class="space-y-6 rounded-4xl bg-surface p-6 ring-1 ring-surface-hover/50 sm:p-8">
						<div class="flex items-center justify-between">
							<h4 class="text-lg font-bold">Recent System Alerts</h4>
							<Button variant="ghost" color="secondary" class="-mr-2">View All</Button>
						</div>
						<div class="space-y-2">
							<div
								class="group flex items-center justify-between rounded-2xl p-4 transition-colors hover:bg-background"
							>
								<div class="flex items-center gap-4">
									<div
										class="flex size-10 items-center justify-center rounded-full bg-destructive-tonal text-on-destructive-tonal"
									>
										<Trash class="size-4.5" />
									</div>
									<div>
										<p class="text-sm font-semibold text-foreground">Legacy tokens removed</p>
										<p class="text-xs text-foreground/50">2 hours ago via system</p>
									</div>
								</div>
								<div class="opacity-0 transition-opacity group-hover:opacity-100">
									<Button variant="outline" size="sm" color="destructive">Review</Button>
								</div>
							</div>
							<div
								class="group flex items-center justify-between rounded-2xl p-4 transition-colors hover:bg-background"
							>
								<div class="flex items-center gap-4">
									<div
										class="flex size-10 items-center justify-center rounded-full bg-success-tonal text-on-success-tonal"
									>
										<Check class="size-4.5" />
									</div>
									<div>
										<p class="text-sm font-semibold text-foreground">Build compiled successfully</p>
										<p class="text-xs text-foreground/50">5 hours ago by Admin</p>
									</div>
								</div>
								<div class="opacity-0 transition-opacity group-hover:opacity-100">
									<Button variant="tonal" size="sm" color="success">Details</Button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Color Palette                      -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-8" id="colors">
		<div class="space-y-2 text-center">
			<h2 class="text-2xl font-bold tracking-tight">Core Tokens</h2>
			<p class="text-sm text-foreground/60">
				The unopinionated raw color scales defining the application.
			</p>
		</div>

		<div
			class="grid grid-cols-1 gap-8 rounded-[2.5rem] bg-surface p-8 shadow-sm ring-1 ring-surface-hover/50 sm:p-12 md:grid-cols-2"
		>
			{#each colorTokens as group}
				<div class="space-y-4">
					<h3 class="text-sm font-bold tracking-widest text-foreground/40 uppercase">
						{group.group}
					</h3>
					<div class="grid grid-cols-2 gap-4">
						{#each group.tokens as token}
							<div
								class="overflow-hidden rounded-2xl shadow-sm ring-1 ring-foreground/5 transition-transform hover:-translate-y-0.5"
							>
								<div
									class="{token.bg} {token.fg} flex h-24 items-center justify-center text-lg font-bold"
								>
									Aa
								</div>
								<div class="bg-background px-4 py-3">
									<p class="text-xs font-bold text-foreground">{token.label}</p>
									<p class="mt-0.5 font-mono text-[10px] text-foreground/50">{token.name}</p>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</section>
</div>
