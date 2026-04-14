<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import Trash from '@tabler/icons-svelte-runes/icons/trash';
	import ArrowRight from '@tabler/icons-svelte-runes/icons/arrow-right';
	import Mail from '@tabler/icons-svelte-runes/icons/mail';
</script>

<svelte:head>
	<title>Button — Design System</title>
</svelte:head>

<div class="space-y-16">
	<!-- HEADER -->
	<header class="space-y-6">
		<div class="space-y-4">
			<h1 class="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">Button</h1>
			<p class="max-w-2xl text-xl leading-relaxed text-foreground/60">
				Interactive elements designed for seamless interactions. Supports multiple variants, colors,
				sizes, and icon compositions with built-in accessibility and press feedback.
			</p>
		</div>
		<div class="flex items-center gap-3 pt-2">
			<Button color="primary" variant="filled">Get Started</Button>
			<Button color="secondary" variant="tonal">Component API</Button>
		</div>
	</header>

	<!-- MAIN SHOWCASE HERO -->
	<div
		class="relative flex min-h-[350px] items-center justify-center overflow-hidden rounded-[2.5rem] border border-foreground/5 bg-surface p-12 shadow-sm ring-1 ring-surface-hover/50"
	>
		<div
			class="pointer-events-none absolute -top-32 -right-32 size-[400px] rounded-full bg-primary/5 blur-3xl"
		></div>

		<div class="relative z-10 flex flex-wrap items-center justify-center gap-6">
			<Button size="lg" color="primary" variant="filled">Create Project</Button>
			<Button size="lg" color="secondary" variant="outline">View Settings</Button>
			<Button size="lg" color="destructive" variant="ghost">Delete Container</Button>
		</div>
	</div>

	<!-- USAGE / ANATOMY -->
	<section class="space-y-8">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Hierarchy & Variants</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				Use different variants to express the hierarchy of actions. A page should typically have
				only one prominent primary action.
			</p>
		</div>

		<div class="grid grid-cols-1 gap-8 md:grid-cols-2">
			<!-- Filled -->
			<div class="space-y-4">
				<div
					class="flex h-48 flex-col items-center justify-center rounded-3xl border border-foreground/5 bg-surface shadow-sm ring-1 ring-surface-hover/50"
				>
					<Button variant="filled" color="primary">Save Changes</Button>
				</div>
				<div>
					<h3 class="font-bold text-foreground">Filled (Primary)</h3>
					<p class="mt-1 text-xs text-foreground/60">
						High emphasis. Used for the primary, most important action on a screen.
					</p>
				</div>
			</div>

			<!-- Tonal -->
			<div class="space-y-4">
				<div
					class="flex h-48 flex-col items-center justify-center rounded-3xl border border-foreground/5 bg-surface shadow-sm ring-1 ring-surface-hover/50"
				>
					<Button variant="tonal" color="secondary">Review Draft</Button>
				</div>
				<div>
					<h3 class="font-bold text-foreground">Tonal (Secondary)</h3>
					<p class="mt-1 text-xs text-foreground/60">
						Medium emphasis. Used for secondary actions that shouldn't visually compete with the
						primary button.
					</p>
				</div>
			</div>

			<!-- Outline -->
			<div class="space-y-4">
				<div
					class="flex h-48 flex-col items-center justify-center rounded-3xl border border-foreground/5 bg-surface shadow-sm ring-1 ring-surface-hover/50"
				>
					<Button variant="outline" color="destructive">Cancel</Button>
				</div>
				<div>
					<h3 class="font-bold text-foreground">Outline</h3>
					<p class="mt-1 text-xs text-foreground/60">
						Medium-low emphasis. Contains actions that are important but not primary.
					</p>
				</div>
			</div>

			<!-- Ghost -->
			<div class="space-y-4">
				<div
					class="flex h-48 flex-col items-center justify-center rounded-3xl border border-foreground/5 bg-surface shadow-sm ring-1 ring-surface-hover/50"
				>
					<Button variant="ghost" color="primary">Learn More</Button>
				</div>
				<div>
					<h3 class="font-bold text-foreground">Ghost</h3>
					<p class="mt-1 text-xs text-foreground/60">
						Low emphasis. Best for optional actions or displaying a list of equal-weight actions.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- COMPOSITIONS -->
	<section class="space-y-8">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Compositions & Icons</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				Buttons can contain text, icons, or a combination of both. The component handles spacing and
				SVG sizing automatically.
			</p>
		</div>

		<div
			class="flex flex-wrap items-end gap-8 rounded-3xl border border-foreground/5 bg-surface p-8 shadow-sm ring-1 ring-surface-hover/50"
		>
			<div class="space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
					Leading Icon
				</p>
				<Button color="primary" variant="filled">
					<Mail /> Send Email
				</Button>
			</div>

			<div class="space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
					Trailing Icon
				</p>
				<Button color="success" variant="tonal">
					Checkout <ArrowRight />
				</Button>
			</div>

			<div class="space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">Icon Only</p>
				<Button size="icon-md" color="secondary" variant="outline">
					<Search />
				</Button>
			</div>

			<div class="space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
					Icon Only (Ghost)
				</p>
				<Button size="icon-md" color="destructive" variant="ghost">
					<Trash />
				</Button>
			</div>
		</div>
	</section>

	<!-- SIZES -->
	<section class="space-y-8">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Sizes</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				Three standardized sizes ensure the button respects the surrounding typographic scale.
			</p>
		</div>

		<div
			class="flex flex-col items-start gap-8 rounded-3xl border border-foreground/5 bg-surface p-8 shadow-sm ring-1 ring-surface-hover/50 md:flex-row md:items-end"
		>
			<div class="w-[150px] space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">Small (sm)</p>
				<Button size="sm" variant="filled">Action</Button>
			</div>
			<div class="w-[150px] space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
					Medium (md)
				</p>
				<Button size="md" variant="filled">Action</Button>
			</div>
			<div class="w-[150px] space-y-3">
				<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">Large (lg)</p>
				<Button size="lg" variant="filled">Action</Button>
			</div>
		</div>
	</section>

	<!-- DARK CONTEXT -->
	<section class="space-y-8">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Dark Surfaces</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				The component inherently guarantees contrast and accessibility when placed on dark or
				high-contrast surfaces.
			</p>
		</div>

		<div
			class="relative overflow-hidden rounded-[2.5rem] bg-foreground p-12 text-background shadow-2xl"
		>
			<div
				class="pointer-events-none absolute -top-20 -right-20 size-80 rounded-full bg-primary/20 blur-3xl"
			></div>
			<div
				class="pointer-events-none absolute -bottom-20 -left-20 size-60 rounded-full bg-secondary/15 blur-3xl"
			></div>

			<div class="relative z-10 grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-4">
				<div class="space-y-3">
					<p class="text-[10px] font-bold tracking-widest text-background/50 uppercase">Filled</p>
					<Button color="primary" variant="filled">Primary</Button>
				</div>
				<div class="space-y-3">
					<p class="text-[10px] font-bold tracking-widest text-background/50 uppercase">Outline</p>
					<Button color="primary" variant="outline">Secondary</Button>
				</div>
				<div class="space-y-3">
					<p class="text-[10px] font-bold tracking-widest text-background/50 uppercase">Tonal</p>
					<Button color="success" variant="tonal">Confirm</Button>
				</div>
				<div class="space-y-3">
					<p class="text-[10px] font-bold tracking-widest text-background/50 uppercase">Ghost</p>
					<Button color="destructive" variant="ghost">Delete</Button>
				</div>
			</div>
		</div>
	</section>
</div>
