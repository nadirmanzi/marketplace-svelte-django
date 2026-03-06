<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
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

	const colors = ['primary', 'secondary', 'destructive', 'success'] as const;
	const variants = ['filled', 'tonal', 'outline', 'ghost'] as const;
	const sizes = ['sm', 'md', 'lg'] as const;

	const colorTokens = [
		{
			group: 'Primary',
			tokens: [
				{ name: '--color-primary', bg: 'bg-primary', fg: 'text-on-primary', label: 'primary' },
				{ name: '--color-primary-hover', bg: 'bg-primary-hover', fg: 'text-on-primary', label: 'primary-hover' },
				{ name: '--color-primary-tonal', bg: 'bg-primary-tonal', fg: 'text-on-primary-tonal', label: 'primary-tonal' },
				{ name: '--color-primary-tonal-hover', bg: 'bg-primary-tonal-hover', fg: 'text-on-primary-tonal', label: 'primary-tonal-hover' }
			]
		},
		{
			group: 'Secondary',
			tokens: [
				{ name: '--color-secondary', bg: 'bg-secondary', fg: 'text-on-secondary', label: 'secondary' },
				{ name: '--color-secondary-hover', bg: 'bg-secondary-hover', fg: 'text-on-secondary', label: 'secondary-hover' },
				{ name: '--color-secondary-tonal', bg: 'bg-secondary-tonal', fg: 'text-on-secondary-tonal', label: 'secondary-tonal' },
				{ name: '--color-secondary-tonal-hover', bg: 'bg-secondary-tonal-hover', fg: 'text-on-secondary-tonal', label: 'secondary-tonal-hover' }
			]
		},
		{
			group: 'Destructive',
			tokens: [
				{ name: '--color-destructive', bg: 'bg-destructive', fg: 'text-on-destructive', label: 'destructive' },
				{ name: '--color-destructive-hover', bg: 'bg-destructive-hover', fg: 'text-on-destructive', label: 'destructive-hover' },
				{ name: '--color-destructive-tonal', bg: 'bg-destructive-tonal', fg: 'text-on-destructive-tonal', label: 'destructive-tonal' },
				{ name: '--color-destructive-tonal-hover', bg: 'bg-destructive-tonal-hover', fg: 'text-on-destructive-tonal', label: 'destructive-tonal-hover' }
			]
		},
		{
			group: 'Success',
			tokens: [
				{ name: '--color-success', bg: 'bg-success', fg: 'text-on-success', label: 'success' },
				{ name: '--color-success-hover', bg: 'bg-success-hover', fg: 'text-on-success', label: 'success-hover' },
				{ name: '--color-success-tonal', bg: 'bg-success-tonal', fg: 'text-on-success-tonal', label: 'success-tonal' },
				{ name: '--color-success-tonal-hover', bg: 'bg-success-tonal-hover', fg: 'text-on-success-tonal', label: 'success-tonal-hover' }
			]
		},
		{
			group: 'Surfaces',
			tokens: [
				{ name: '--color-background', bg: 'bg-background', fg: 'text-foreground', label: 'background' },
				{ name: '--color-foreground', bg: 'bg-foreground', fg: 'text-background', label: 'foreground' },
				{ name: '--color-surface', bg: 'bg-surface', fg: 'text-on-surface', label: 'surface' }
			]
		}
	];
</script>

<svelte:head>
	<title>Design System — UI Showcase</title>
</svelte:head>

<!-- ─── PAGE WRAPPER ─── -->
<div class="mx-auto max-w-6xl space-y-16 px-6 py-12">

	<!-- ─── HEADER ─── -->
	<header class="space-y-2">
		<h1 class="text-3xl font-bold tracking-tight">Design System</h1>
		<p class="text-foreground/60 text-sm">Visual reference for all tokens, components, and variants.</p>
	</header>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Color Palette                      -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-6" id="colors">
		<div class="space-y-1">
			<h2 class="text-xl font-semibold">Color Palette</h2>
			<p class="text-foreground/50 text-xs">All theme tokens with their foreground pairings.</p>
		</div>

		{#each colorTokens as group}
			<div class="space-y-2">
				<h3 class="text-sm font-medium text-foreground/70">{group.group}</h3>
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
					{#each group.tokens as token}
						<div class="overflow-hidden rounded-xl border border-foreground/5">
							<div class="{token.bg} {token.fg} flex h-20 items-center justify-center text-xs font-medium">
								Aa
							</div>
							<div class="bg-surface px-3 py-2">
								<p class="text-xs font-medium text-on-surface">{token.label}</p>
								<p class="text-[10px] text-foreground/40 font-mono">{token.name}</p>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</section>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Buttons                            -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-8" id="buttons">
		<div class="space-y-1">
			<h2 class="text-xl font-semibold">Buttons</h2>
			<p class="text-foreground/50 text-xs">All color × variant combinations, sizes, icon usage, on background and surface.</p>
		</div>

		<!-- ── Color × Variant Matrix (on background) ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">On Background</h3>
			<div class="rounded-2xl border border-foreground/5 bg-background p-6">
				<div class="grid grid-cols-4 gap-x-6 gap-y-3">
					<!-- Header row -->
					{#each colors as c}
						<p class="text-center text-[10px] font-semibold uppercase tracking-widest text-foreground/40">{c}</p>
					{/each}

					<!-- Variant rows -->
					{#each variants as v}
						{#each colors as c}
							<div class="flex justify-center">
								<Button color={c} variant={v}>{v}</Button>
							</div>
						{/each}
					{/each}
				</div>
			</div>
		</div>

		<!-- ── Color × Variant Matrix (on surface) ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">On Surface</h3>
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<div class="grid grid-cols-4 gap-x-6 gap-y-3">
					{#each colors as c}
						<p class="text-center text-[10px] font-semibold uppercase tracking-widest text-foreground/40">{c}</p>
					{/each}

					{#each variants as v}
						{#each colors as c}
							<div class="flex justify-center">
								<Button color={c} variant={v}>{v}</Button>
							</div>
						{/each}
					{/each}
				</div>
			</div>
		</div>

		<!-- ── Size Scale ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">Size Scale</h3>
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<div class="flex flex-wrap items-end gap-4">
					{#each sizes as s}
						<div class="flex flex-col items-center gap-2">
							<span class="text-[10px] font-medium uppercase tracking-wider text-foreground/40">{s}</span>
							<Button size={s}><Home2 /> Button</Button>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- ── With Icons ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">With Icons</h3>
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<div class="flex flex-wrap gap-3">
					<Button><Search /> Search</Button>
					<Button color="secondary"><ShoppingBag /> Add to Cart</Button>
					<Button color="destructive" variant="outline"><Trash /> Delete</Button>
					<Button color="success"><Check /> Confirm</Button>
					<Button variant="tonal"><Plus /> New Item</Button>
					<Button color="secondary" variant="ghost"><ArrowRight /> Continue</Button>
					<Button variant="outline"><Download /> Export</Button>
					<Button color="secondary" variant="tonal"><Settings /> Settings</Button>
				</div>
			</div>
		</div>

		<!-- ── Icon-Only ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">Icon Only</h3>
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<div class="flex flex-wrap items-center gap-3">
					<Button class="min-w-0! px-2.5!"><Heart /></Button>
					<Button color="secondary" class="min-w-0! px-2.5!"><Search /></Button>
					<Button color="destructive" variant="outline" class="min-w-0! px-2.5!"><Trash /></Button>
					<Button color="success" variant="tonal" class="min-w-0! px-2.5!"><Check /></Button>
					<Button variant="ghost" class="min-w-0! px-2.5!"><Settings /></Button>
					<Button color="secondary" variant="ghost" class="min-w-0! px-2.5!"><Plus /></Button>
				</div>
			</div>
		</div>

		<!-- ── Disabled State ── -->
		<div class="space-y-3">
			<h3 class="text-sm font-medium text-foreground/70">Disabled</h3>
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<div class="flex flex-wrap gap-3">
					<Button disabled>Filled</Button>
					<Button variant="tonal" disabled>Tonal</Button>
					<Button variant="outline" disabled>Outline</Button>
					<Button variant="ghost" disabled>Ghost</Button>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Surfaces                           -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-6" id="surfaces">
		<div class="space-y-1">
			<h2 class="text-xl font-semibold">Surfaces</h2>
			<p class="text-foreground/50 text-xs">Background vs surface layering with correct text pairings.</p>
		</div>

		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<!-- Background -->
			<div class="rounded-2xl border border-foreground/5 bg-background p-6">
				<p class="text-sm font-semibold text-foreground">Background</p>
				<p class="text-xs text-foreground/60">bg-background + text-foreground</p>
				<div class="mt-4 rounded-xl bg-surface p-4">
					<p class="text-sm font-semibold text-on-surface">Surface Card</p>
					<p class="text-xs text-on-surface/60">bg-surface + text-on-surface</p>
					<div class="mt-3 flex gap-2">
						<Button size="sm">Action</Button>
						<Button size="sm" variant="ghost" color="secondary">Cancel</Button>
					</div>
				</div>
			</div>

			<!-- Surface full -->
			<div class="rounded-2xl border border-foreground/5 bg-surface p-6">
				<p class="text-sm font-semibold text-on-surface">Surface Panel</p>
				<p class="text-xs text-on-surface/60">Full surface with nested elements</p>
				<div class="mt-4 flex flex-col gap-3">
					<div class="rounded-lg bg-background p-3">
						<p class="text-xs text-foreground/70">Inset area (bg-background)</p>
					</div>
					<div class="flex gap-2">
						<Button size="sm" color="success"><Check /> Save</Button>
						<Button size="sm" variant="outline" color="destructive"><Trash /> Discard</Button>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Typography (placeholder for now)   -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-6" id="typography">
		<div class="space-y-1">
			<h2 class="text-xl font-semibold">Typography</h2>
			<p class="text-foreground/50 text-xs">Font scale and weight reference.</p>
		</div>

		<div class="rounded-2xl border border-foreground/5 bg-surface p-6 space-y-4">
			<p class="text-3xl font-bold tracking-tight">Heading 1 — 3xl bold</p>
			<p class="text-2xl font-semibold">Heading 2 — 2xl semibold</p>
			<p class="text-xl font-semibold">Heading 3 — xl semibold</p>
			<p class="text-base font-medium">Body Large — base medium</p>
			<p class="text-sm">Body — sm regular</p>
			<p class="text-xs text-foreground/60">Caption — xs muted</p>
			<p class="text-[10px] font-mono text-foreground/40">Overline — 10px mono</p>
		</div>
	</section>

	<!-- ═══════════════════════════════════════════ -->
	<!-- SECTION: Future Components Placeholder      -->
	<!-- ═══════════════════════════════════════════ -->
	<section class="space-y-6" id="components">
		<div class="space-y-1">
			<h2 class="text-xl font-semibold">Components</h2>
			<p class="text-foreground/50 text-xs">Future components will be showcased here.</p>
		</div>

		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each ['Input', 'Select', 'Checkbox', 'Toggle', 'Modal', 'Toast', 'Badge', 'Avatar', 'Card'] as component}
				<div class="flex h-32 items-center justify-center rounded-2xl border-2 border-dashed border-foreground/10 text-sm text-foreground/30">
					{component}
				</div>
			{/each}
		</div>
	</section>

	<!-- Footer spacer -->
	<div class="h-8"></div>
</div>
