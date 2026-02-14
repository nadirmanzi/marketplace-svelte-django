<script lang="ts">
	type ProductProps = {
		product: {
			name: string;
			seller: string;
			description: string;
			price: number;
			discount_price: number;
		};
	};

	const product: ProductProps = $props();
</script>

<div class="relative max-w-60 overflow-hidden rounded-lg bg-white p-1">
	<div class="h-50 w-full">
		<img
			src="/hero2.jpg"
			alt={product.product.name}
			class="h-full w-full rounded-lg object-cover"
		/>
	</div>

	<div class="w-full space-y-4 p-1 backdrop-blur-lg">
		<div class="">
			<p class="max-w-full truncate font-semibold">
				{product.product.name} dasd sad sa dsa da sd sad a
			</p>
			<p class="text-sm text-text-secondary">{product.product.seller}</p>
		</div>

		<div class="">
			<p class="font-semibold font-sans">{product.product.price} Rwf</p>
		</div>
	</div>
</div>
