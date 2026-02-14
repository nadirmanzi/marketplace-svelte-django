<script lang="ts">
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { ChevronRight, ShoppingBag } from '@lucide/svelte';
	import CartProductCard from './cart-product-card.svelte';
	import Separator from './ui/separator/separator.svelte';

	const products = [
		{
			id: '#123456789',
			seller: 'Seller A',
			name: 'Product 1',
			price: 23000,
			quantity: 2,
			imageUrl: '/images/product1.jpg'
		},
		{
			id: '#987654321',
			seller: 'Seller B',
			name: 'Product 2',
			price: 12900,
			quantity: 1,
			imageUrl: '/images/product2.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		},
		{
			id: '#456789123',
			seller: 'Seller C',
			name: 'Product 3',
			price: 19200,
			quantity: 5,
			imageUrl: '/images/product3.jpg'
		}
	];
</script>

<Sheet.Root open={false}>
	<Sheet.Trigger>
		<Button variant="ghost" size="icon">
			<ShoppingBag class="size-4" strokeWidth={1.8} />
		</Button>
	</Sheet.Trigger>
	<Sheet.Content class="w-120">
		<div class="flex h-full flex-col">
			<Sheet.Header class="flex-none gap-2">
				<Sheet.Title>My shopping cart</Sheet.Title>
				<Sheet.Description>You have 8 orders in your cart.</Sheet.Description>
			</Sheet.Header>

			<Sheet.Header class="flex-1 overflow-y-auto bg-background py-0">
				{#each products as product, index}
					<CartProductCard
						id={product.id}
						seller={product.seller}
						name={product.name}
						price={product.price}
						quantity={product.quantity}
						imageUrl={product.imageUrl}
					/>

					{#if !(index === products.length - 1)}
						<Separator class="bg-border" />
					{/if}
				{/each}
			</Sheet.Header>

			<Sheet.Footer class="flex-none">
				<Sheet.Title class="flex justify-between">
					<span>Total</span>
					<span>$559.00</span>
				</Sheet.Title>
				<Button class="w-full">
					<p>Proceed to checkout</p>
					<ChevronRight class="size-4" strokeWidth={1.8} />
				</Button>
			</Sheet.Footer>
		</div>
	</Sheet.Content>
</Sheet.Root>
