<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Trash2, Plus, Minus, Search } from '@lucide/svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import Input from './ui/input/input.svelte';

	type ProductProps = {
		id: string;
		seller: string;
		name: string;
		price: number;
		quantity: number;
		imageUrl: string;
	};

	let { id, seller, name, price, quantity, imageUrl }: ProductProps = $props();
</script>

<div class="grid grid-cols-2 rounded-lg">
	<div class="flex gap-4">
		<!-- IMAGE -->
		<div class="h-24 w-24 rounded-lg bg-ghost"></div>

		<!-- PRODUCT DETAILS -->
		<div class="flex flex-col justify-between">
			<div>
				<p class="text-base font-semibold">{name}</p>
				<p class="text-xs text-foreground-secondary">{id}</p>
			</div>

			<p class="text-sm font-bold">{price} Rwf</p>
		</div>
	</div>

	<div class="flex flex-col justify-between">
		<!-- DELETE -->
		<div class="flex justify-end">
			<Button variant="ghost" size="icon-sm" class="text-destructive">
				<Trash2
					class="size-4"
					strokeWidth={1.8}
					fill-opacity={0.3}
					fill="var(--color-destructive)"
				/>
			</Button>
		</div>

		<!-- QUANTITY CONTROLS -->
		<div class="flex justify-end">
			<div
				class="flex items-center justify-between overflow-hidden rounded-full bg-ghost"
			>
				<Button
					variant="ghost"
					size="icon-sm"
					onclick={() => {
						if (quantity > 0) quantity -= 1;
					}}
					class="rounded-none p-0 hover:bg-ghost-secondary focus-visible:bg-ghost-secondary-active"
				>
					<Minus class="size-4" strokeWidth={1.8} />
				</Button>
				<Input
					bind:value={quantity}
					type="number"
					min="1"
					max="99"
					class="h-full bg-transparent w-14 [appearance:textfield] rounded-none border-none text-center hover:bg-ghost-secondary focus-visible:border-transparent focus-visible:bg-ghost-active focus-visible:ring-0 focus-visible:ring-offset-0 [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:m-0 [&::-webkit-outer-spin-button]:appearance-none"
				/>
				<Button
					variant="ghost"
					size="icon-sm"
					onclick={() => {
						if (quantity < 99) quantity += 1;
					}}
					class="rounded-none p-0 hover:bg-ghost-secondary focus-visible:bg-ghost-secondary-active"
				>
					<Plus class="size-4" strokeWidth={1.8} />
				</Button>
			</div>
		</div>
	</div>
</div>
