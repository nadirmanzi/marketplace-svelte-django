<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Trash2, Plus, Minus, Search } from '@lucide/svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import Input from '$lib/components/ui/input/input.svelte';
	import Separator from '$lib/components/ui/separator/separator.svelte';
	import { fade, slide, scale, fly } from 'svelte/transition';
	import { cubicOut } from 'svelte/easing';
	import type { TransitionConfig } from 'svelte/transition';

	type CartProductProps = {
		id: string;
		seller: string;
		name: string;
		price: number;
		quantity: number;
		imageUrl: string;
		index: number;
		total_products: number;
		// open_sheet: boolean;
	};

	interface SlideFadeParams {
		delay?: number;
		duration?: number;
		easing?: (t: number) => number;
		x?: number;
		y?: number;
	}

	let { id, seller, name, price, quantity, imageUrl, index, total_products }: CartProductProps =
		$props();

	let is_odd = $derived(index % 2 === 0);
</script>

<div class={`grid grid-cols-2 p-4`}>
	<div class="flex gap-4">
		<!-- IMAGE -->

		<div class="h-24 w-24 rounded-lg bg-ghost"></div>

		<!-- PRODUCT DETAILS -->
		<div class="flex flex-col justify-between">
			<div>
				<p class="text-base font-semibold">
					{name}
				</p>
				<p class="text-xs text-foreground-secondary">
					{seller}
				</p>
			</div>

			<p class="text-sm font-bold">
				{price} Rwf
			</p>
		</div>
	</div>

	<div class="flex flex-col justify-between">
		<!-- DELETE -->
		<div class="flex justify-end">
			<Button variant="destructive-ghost" size="icon-sm" class="">
				<Trash2 class="size-4" strokeWidth={1.8} fill-opacity={0.3} />
			</Button>
		</div>

		<!-- QUANTITY CONTROLS -->
		<div class={`flex max-h-8 items-center self-end overflow-hidden rounded-full bg-ghost`}>
			<Button
				variant="ghost"
				size="icon-sm"
				onclick={() => {
					if (quantity > 0) quantity -= 1;
				}}
				class="rounded-l-full rounded-r-none"
			>
				<Minus class="size-4" strokeWidth={1.8} />
			</Button>
			<Input
				bind:value={quantity}
				type="number"
				min="1"
				max="99"
				disabled={true}
				class="h-full w-10 [appearance:textfield] rounded-none border-none bg-transparent text-center focus-visible:border-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 disabled:cursor-auto disabled:opacity-100 [&::-webkit-inner-spin-button]:m-0 [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:m-0 [&::-webkit-outer-spin-button]:appearance-none"
			/>

			<Button
				variant="ghost"
				size="icon-sm"
				onclick={() => {
					if (quantity < 99) quantity += 1;
				}}
				class="rounded-l-none rounded-r-full"
			>
				<Plus class="size-4" strokeWidth={1.8} />
			</Button>
		</div>
		<!-- </div> -->
	</div>
</div>

<div class="px-4">
	{#if index < total_products - 1}
		<Separator />
	{/if}
</div>
