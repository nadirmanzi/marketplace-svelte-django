<script lang="ts">
	import Button from '$lib/components/ui/button/button.svelte';
	import Input from '$lib/components/ui/input/input.svelte';
	import { Search, User } from '@lucide/svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index.js';
	import ProductCard from '$lib/components/product-card.svelte';

	const products = [
		{
			seller: 'Seller A',
			name: 'Product 1',
			price: 23000,
			description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
			discount_price: 250
		},
		// {
		// 	seller: 'Seller B',
		// 	name: 'Product 2',
		// 	price: 12900,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// },
		// {
		// 	seller: 'Seller C',
		// 	name: 'Product 3',
		// 	price: 19200,
		// 	description: 'knd9823hdinj dajsnd dijsandijsa dijad  doisandiusandia dsnn sadasjd',
		// 	discount_price: 250
		// }
	];
</script>

<svelte:head>
	<title>[Marketplace] | Shop</title>
</svelte:head>

<!-- <h4 class="text-foreground">Foreground primary</h4>
<h4 class="text-foreground-secondary">Foreground secondary</h4> -->

<!-- <div class="grid w-full grid-cols-2">
	<div class="">
		<div class="space-y-4 bg-background p-4">
			<h1 class="font-bold">Buttons</h1>

			<div class="flex flex-wrap space-x-2">
				<Button variant="primary">Primary</Button>
				<Button variant="secondary">Secondary</Button>
				<Button variant="ghost">ghost</Button>
				<Button variant="outline">outline</Button>
				<Button variant="destructive">destructive</Button>
				<Button variant="success">success</Button>
			</div>
		</div>

		<div class="space-y-4 bg-background p-4">
			<h1 class="font-bold">Button size</h1>

			<div class="flex flex-wrap items-center space-x-2">
				<Button variant="primary" size="lg">
					<User />
					<p>Large</p>
				</Button>
				<Button variant="primary">
					<User />
					<p>Default</p>
				</Button>
				<Button variant="primary" size="sm">
					<User />
					<p>Small</p>
				</Button>
				<Button variant="primary" size="icon-lg"><User /></Button>
				<Button variant="primary" size="icon"><User /></Button>
				<Button variant="primary" size="icon-sm"><User /></Button>
			</div>
		</div>

		<div class="space-y-4 bg-background p-4">
			<h1 class="font-bold">Input</h1>

			<div class="flex flex-wrap items-center space-x-2">
				<InputGroup.Root>
					<InputGroup.Input placeholder="Search..." class="w-10" />
					<InputGroup.Addon align="inline-start">
						<Search class="h-4 w-4" strokeWidth={1.8} />
					</InputGroup.Addon>
					<InputGroup.Addon align="inline-end">
						<Search class="h-4 w-4" strokeWidth={1.8} />
					</InputGroup.Addon>
				</InputGroup.Root>
			</div>
		</div>
	</div>

	<div class="space-y-4 bg-background-secondary p-4">
		<h1 class="font-bold">Buttons</h1>

		<div class="flex flex-wrap space-x-2">
			<Button variant="primary">Primary</Button>
			<Button variant="secondary">Secondary</Button>
			<Button variant="ghost-secondary">ghost sec</Button>
			<Button variant="outline-secondary">outline sec</Button>
			<Button variant="destructive">destructive</Button>
			<Button variant="success">success</Button>
		</div>
	</div>
</div> -->

<div class="gap-4 p-4 bg-background-secondary min-h-dvh">
	<p class="font-bold">Product card</p>

	<div class='space-y-4'>
		{#each products as product, i}
			<ProductCard {product} />
		{/each}
	</div>
</div>
