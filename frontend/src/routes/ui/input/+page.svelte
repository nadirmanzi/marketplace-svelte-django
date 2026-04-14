<script lang="ts">
	import Input from '$lib/components/ui/input.svelte';
	import Search from '@tabler/icons-svelte-runes/icons/search';
	import User from '@tabler/icons-svelte-runes/icons/user';
	import Mail from '@tabler/icons-svelte-runes/icons/mail';
	import Eye from '@tabler/icons-svelte-runes/icons/eye';
	import EyeOff from '@tabler/icons-svelte-runes/icons/eye-off';
	import CircleCheck from '@tabler/icons-svelte-runes/icons/circle-check-filled';
	import AlertCircle from '@tabler/icons-svelte-runes/icons/alert-circle-filled';

	let showPassword = $state(false);
</script>

<svelte:head>
	<title>Input — Design System</title>
</svelte:head>

<div class="space-y-16">
	<!-- HEADER -->
	<header class="space-y-6">
		<div class="space-y-4">
			<h1 class="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl">Input</h1>
			<p class="max-w-2xl text-xl leading-relaxed text-foreground/60">
				A pure, context-aware input pill. No complex variants—just clean architecture that automatically calculates the perfect background, hover, and border interaction depending on its surface.
			</p>
		</div>
	</header>

	<!-- MAIN SHOWCASE HERO -->
	<div
		class="relative flex items-center justify-center overflow-hidden rounded-[2.5rem] border border-foreground/5 bg-surface p-8 ring-1 ring-surface-hover/50 md:p-16"
	>
		<div
			class="pointer-events-none absolute -bottom-32 left-10 size-[300px] rounded-full bg-secondary/5 blur-3xl"
		></div>

		<div class="relative z-10 w-full max-w-md space-y-4">
			<Input
				type="email"
				placeholder="you@example.com"
				label="Work Email"
				size="lg"
				context="surface"
			>
				{#snippet leading()}
					<Mail />
				{/snippet}
			</Input>
			<Input
				type={showPassword ? 'text' : 'password'}
				placeholder="Enter password…"
				label="Password"
				size="lg"
				context="surface"
			>
				{#snippet trailing()}
					<button
						onclick={() => (showPassword = !showPassword)}
						class="text-foreground/40 transition-colors hover:text-foreground"
					>
						{#if showPassword}
							<EyeOff class="size-4" />
						{:else}
							<Eye class="size-4" />
						{/if}
					</button>
				{/snippet}
			</Input>
		</div>
	</div>

	<!-- THE CONTEXT ARCHITECTURE (VISUAL CONTEXTS) -->
	<section class="space-y-8">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Strict Context Rendering</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				The component has no <code>variant</code> prop. Instead, you declare the <code>context</code> (the container it lives in) and it strictly enforces perfect contrast. Hovering adds subtle grey fills, and active states turn the borders stark black.
			</p>
		</div>

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
			<!-- On Grey Background -->
			<div class="flex flex-col space-y-4">
				<div
					class="flex min-h-[250px] flex-1 flex-col items-center justify-center rounded-4xl border-2 border-dashed border-foreground/10 bg-background p-8 shadow-inner ring-1 ring-foreground/10"
				>
					<div class="w-full max-w-xs space-y-4">
						<Input
							context="background"
							placeholder="Focus me..."
							label="Background Default"
						>
							{#snippet leading()}<User />{/snippet}
						</Input>
					</div>
				</div>
				<div class="px-2">
					<h3 class="font-bold text-foreground">Context: <code>"background"</code></h3>
					<p class="mt-1 text-xs leading-relaxed text-foreground/60">
						When placed directly on the application's base grey surface <code>bg-background</code>, the input is pure white. Hovering adds a slight grey fill. Focus punches to a solid black border.
					</p>
				</div>
			</div>

			<!-- On White Surface -->
			<div class="flex flex-col space-y-4">
				<div
					class="flex min-h-[250px] flex-1 flex-col items-center justify-center rounded-4xl bg-surface p-8 shadow-xl ring-1 ring-foreground/5"
				>
					<div class="w-full max-w-xs space-y-4">
						<Input
							context="surface"
							placeholder="Focus me..."
							label="Surface Default"
						>
							{#snippet leading()}<User />{/snippet}
						</Input>
					</div>
				</div>
				<div class="px-2">
					<h3 class="font-bold text-foreground">Context: <code>"surface"</code></h3>
					<p class="mt-1 text-xs leading-relaxed text-foreground/60">
						When placed inside a white card <code>bg-surface</code>, the input adopts a grey fill to step back from the card surface. Hovering darkens the grey slightly.
					</p>
				</div>
			</div>

			<!-- On Dark Foreground -->
			<div class="flex flex-col space-y-4 lg:col-span-2">
				<div
					class="flex w-full flex-col items-center justify-center rounded-4xl bg-foreground p-8 md:p-12 shadow-2xl"
				>
					<div class="w-full max-w-md">
						<Input
							context="dark"
							placeholder="Search global registry..."
							label="Dark Default"
						>
							{#snippet leading()}<Search />{/snippet}
						</Input>
					</div>
				</div>
				<div class="px-2">
					<h3 class="font-bold text-foreground">Context: <code>"dark"</code> (e.g. Navigation)</h3>
					<p class="mt-1 max-w-3xl text-xs leading-relaxed text-foreground/60">
						When placed on stark black surfaces like the main top navigation, the input retains a white/grey pill format but adjusts its internal label/helper tokens to be legible against the black exterior.
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- VALIDATION STATES -->
	<section class="space-y-8 pt-6">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Validation States</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				Visual enforcement for success and destructive interactions. Passed as a boolean for success
				or a string for error detailing.
			</p>
		</div>

		<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
			<div class="space-y-4 rounded-3xl bg-surface p-8 ring-1 ring-surface-hover/50">
				<Input
					context="surface"
					placeholder="hello@company"
					label="Workspace Email"
					value="hello@company"
					error="Please include a valid top-level domain."
				>
					{#snippet trailing()}
						<AlertCircle class="text-destructive" />
					{/snippet}
				</Input>
			</div>
			<div class="space-y-4 rounded-3xl bg-surface p-8 ring-1 ring-surface-hover/50">
				<Input
					context="surface"
					placeholder="username"
					label="Available Handle"
					value="nadirmanzi"
					success={true}
					helperText="That username is available!"
				>
					{#snippet trailing()}
						<CircleCheck class="text-success" />
					{/snippet}
				</Input>
			</div>
		</div>
	</section>

	<!-- SIZING -->
	<section class="space-y-8 pt-6">
		<div class="space-y-2">
			<h2 class="text-2xl font-bold tracking-tight text-foreground">Sizing</h2>
			<p class="max-w-3xl text-sm text-foreground/60">
				Inputs conform to three rigid heights tying directly to typographic baselines. Flanking icons scale natively alongside text.
			</p>
		</div>

		<div class="rounded-3xl bg-surface p-8 ring-1 ring-surface-hover/50">
			<div class="flex max-w-3xl flex-col items-end gap-6 md:flex-row">
				<div class="w-full space-y-2">
					<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
						Small (h-8)
					</p>
					<Input size="sm" context="surface" placeholder="Filter...">
						{#snippet leading()}<Search />{/snippet}
					</Input>
				</div>
				<div class="w-full space-y-2">
					<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
						Medium (h-10)
					</p>
					<Input size="md" context="surface" placeholder="Filter...">
						{#snippet leading()}<Search />{/snippet}
					</Input>
				</div>
				<div class="w-full space-y-2">
					<p class="text-[10px] font-bold tracking-widest text-foreground/40 uppercase">
						Large (h-12)
					</p>
					<Input size="lg" context="surface" placeholder="Filter...">
						{#snippet leading()}<Search />{/snippet}
					</Input>
				</div>
			</div>
		</div>
	</section>
</div>
