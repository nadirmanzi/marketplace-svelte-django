<script lang="ts">
	import Sheet from '$lib/components/ui/sheet.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import ShoppingBag from '@tabler/icons-svelte-runes/icons/shopping-bag';
	import Package from '@tabler/icons-svelte-runes/icons/package';
	import Settings from '@tabler/icons-svelte-runes/icons/settings';

	let isBasicOpen = $state(false);
	let isCustomOpen = $state(false);
	let isFullOpen = $state(false);
</script>

<div class="container mx-auto px-6 py-24">
	<div class="mb-12 flex flex-col gap-4">
		<h1 class="text-4xl font-bold tracking-tight text-foreground">Sheet component</h1>
		<p class="max-w-2xl text-lg text-foreground/60">
			A slide-over sidebar for contextual content, with sticky sections, soft-blur overlays, and
			responsive sizing.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-8 md:grid-cols-3">
		<!-- Basic Usage -->
		<div
			class="flex flex-col gap-4 rounded-3xl border border-foreground/5 bg-surface p-8 shadow-sm"
		>
			<h2 class="text-xl font-bold">Standard Cart</h2>
			<p class="text-sm text-foreground/60">
				The default configuration used in the navigation bar for shopping bag management.
			</p>
			<Button onclick={() => (isBasicOpen = true)} class="mt-4">Open Cart Sheet</Button>
		</div>

		<!-- Custom Side -->
		<div
			class="flex flex-col gap-4 rounded-3xl border border-foreground/5 bg-surface p-8 shadow-sm"
		>
			<h2 class="text-xl font-bold">Settings Side</h2>
			<p class="text-sm text-foreground/60">
				Demonstrating left-side orientation and custom header content.
			</p>
			<Button variant="outline" onclick={() => (isCustomOpen = true)} class="mt-4">
				Open Left Sheet
			</Button>
		</div>

		<!-- Full Body -->
		<div
			class="flex flex-col gap-4 rounded-3xl border border-foreground/5 bg-surface p-8 shadow-sm"
		>
			<h2 class="text-xl font-bold">Rich Content</h2>
			<p class="text-sm text-foreground/60">
				Testing long scrollable lists and complex sticky footers.
			</p>
			<Button variant="outline" onclick={() => (isFullOpen = true)} class="mt-4">
				Open Rich Sheet
			</Button>
		</div>
	</div>

	<!-- ─── SHEET EXAMPLES ─── -->

	<!-- 1. Basic (Cart) -->
	<Sheet bind:open={isBasicOpen}>
		{#snippet header()}
			<div class="flex flex-col">
				<h3 class="text-lg font-bold">Your Bag</h3>
				<p class="text-xs text-foreground/50">3 items selected</p>
			</div>
		{/snippet}
		{#snippet body()}
			<div class="flex flex-col gap-6 pt-4">
				{#each Array(3) as _, i}
					<div class="flex gap-4">
						<div class="size-20 shrink-0 rounded-2xl bg-foreground/5"></div>
						<div class="flex flex-col justify-center gap-1">
							<p class="font-bold">Premium Leather Jacket</p>
							<p class="text-sm text-wrap text-foreground/50">Midnight Black • Medium</p>
							<p class="mt-1 text-sm font-bold text-primary">$299.00</p>
						</div>
					</div>
				{/each}
			</div>
		{/snippet}
		{#snippet footer()}
			<Button class="w-full" size="lg">Checkout ($897.00)</Button>
		{/snippet}
	</Sheet>

	<!-- 2. Custom (Settings/Left) -->
	<Sheet bind:open={isCustomOpen} side="left">
		{#snippet header()}
			<h3 class="text-lg font-bold">Account Settings</h3>
		{/snippet}
		{#snippet body()}
			<div class="space-y-2">
				<Button variant="ghost" class="w-full justify-start gap-3">
					<Settings class="size-4" /> Personal Info
				</Button>
				<Button variant="ghost" class="w-full justify-start gap-3">
					<Package class="size-4" /> Order History
				</Button>
			</div>
		{/snippet}
	</Sheet>

	<!-- 3. Rich Content -->
	<Sheet bind:open={isFullOpen}>
		{#snippet header()}
			<h3 class="text-lg font-bold">Privacy Policy</h3>
		{/snippet}
		{#snippet body()}
			<div class="space-y-6 text-sm leading-relaxed text-foreground/70">
				<p>
					Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt
					ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
					ullamco laboris nisi ut aliquip ex ea commodo consequat.
				</p>
				{#each Array(10) as _}
					<p>
						Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
						nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
						officia deserunt mollit anim id est laborum.
					</p>
				{/each}
			</div>
		{/snippet}
		{#snippet footer()}
			<div class="flex gap-3">
				<Button variant="outline" class="flex-1" onclick={() => (isFullOpen = false)}
					>Decline</Button
				>
				<Button class="flex-1" onclick={() => (isFullOpen = false)}>Accept Terms</Button>
			</div>
		{/snippet}
	</Sheet>
</div>
