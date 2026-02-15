<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronRight, ShoppingBag } from '@lucide/svelte';
	import CartProductCard from '../cart-product-card.svelte';
	import Separator from '$lib/components/ui/separator/separator.svelte';
	import { fade, slide } from 'svelte/transition';

	const PRODUCTS = $state([
		{
			id: '#3123',
			seller: 'Seller A',
			name: 'Product 1',
			price: 23000,
			quantity: 2,
			imageUrl: '/images/product1.jpg'
		},
		{
			id: '#124',
			seller: 'Seller B',
			name: 'Product 2',
			price: 12900,
			quantity: 1,
			imageUrl: '/images/product2.jpg'
		},
		{
			id: '#364',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#756',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#534321',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#74553',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#12456',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#76986',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#3454',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		}
	]);
</script>

<Sheet.Root>
	<Sheet.Trigger variant="ghost-ghost" size="icon">
		<ShoppingBag class="size-4" strokeWidth={1.8} />
	</Sheet.Trigger>
	<Sheet.Content class="w-120" side="right" forceMount>
		<div class="flex h-full flex-col">
			<Sheet.Header class="flex-none gap-2">
				<Sheet.Title>My shopping cart</Sheet.Title>
				<!-- <Sheet.Description>You have 8 orders in your cart.</Sheet.Description> -->
			</Sheet.Header>

			<div class="flex-1 overflow-x-hidden">
				{#each PRODUCTS as product, index (product.id)}
					<CartProductCard {...product} {index} total_products={PRODUCTS.length} />
					<!-- {#if index < PRODUCTS.length - 1}
						<Separator />
					{/if} -->
				{/each}
			</div>

			<Sheet.Footer class="flex-row items-center justify-between">
				<div class="flex">
					<span class="font-bold"
						>Total: ${PRODUCTS.reduce(
							(total, product) => total + product.price * product.quantity,
							0
						)}</span
					>
				</div>
				<Button variant="primary">
					<p>Checkout</p>
					<ChevronRight class="size-4" strokeWidth={1.8} />
				</Button>
			</Sheet.Footer>
		</div>
	</Sheet.Content>
</Sheet.Root>
