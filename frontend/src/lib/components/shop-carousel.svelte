<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import { Carousel } from '@skeletonlabs/skeleton-svelte';
	import ArrowLeft from '@tabler/icons-svelte-runes/icons/arrow-left';
	import FurnitureImg from '$lib/assets/furniture.jpg';
	import ElectronicsImg from '$lib/assets/electronics.jpg';
	import type { Snippet } from 'svelte';

	interface Slide {
		image: string;
		render?: Snippet;
	}
	const slides: Slide[] = [
		{ image: FurnitureImg, render: FurnitureSnippet },
		{ image: ElectronicsImg, render: ElectronicsSnippet },
		{ image: FurnitureImg, render: FurnitureSnippet },
		{ image: ElectronicsImg, render: ElectronicsSnippet }
	];

	// 1. Define your snippets first
</script>

{#snippet FurnitureSnippet()}
	<div class="max-w-md">
		<p class="font-display text-4xl font-bold">Complete your interior with premium furniture</p>
	</div>
{/snippet}

{#snippet ElectronicsSnippet()}
	<div class="max-w-md">
		<p class="font-display text-4xl font-bold">Cutting edge tech for your daily drive</p>
	</div>
{/snippet}

<section class="h-[50dvh] w-full bg-red-300">
	<div class="flex h-full w-full overflow-hidden bg-black">
		<Carousel
			slideCount={slides.length}
			slidesPerPage={1}
			loop
			allowMouseDrag
			autoplay={{ delay: 5000 }}
			class="relative flex h-full w-full flex-col overflow-hidden"
		>
			<Carousel.ItemGroup class="flex-1">
				{#each slides as slide, i (i)}
					<Carousel.Item
						index={i}
						class="relative flex h-full w-full items-center justify-start overflow-hidden"
					>
						<img
							src={slide.image}
							class="absolute inset-0 h-full w-full bg-center object-cover"
							alt=""
						/>

						<div
							class="to-dark/40 absolute inset-0 z-10 flex w-full items-start bg-linear-[140deg] from-black/70 via-black/20 to-transparent px-12 py-6 text-white"
						>
							{#if slide.render}
								{@render slide.render()}
							{/if}
						</div>
					</Carousel.Item>
				{/each}
			</Carousel.ItemGroup>

			<div class="absolute top-6 right-6 z-20">
				<Carousel.Control class="flex items-center gap-4">
					<Carousel.PrevTrigger>
						<Button
							variant="outline"
							class="border-white/20 bg-white/10 text-white backdrop-blur-md"
						>
							<ArrowLeft class="size-5" />
						</Button>
					</Carousel.PrevTrigger>
					<Carousel.NextTrigger>
						<Button
							variant="outline"
							class="border-white/20 bg-white/10 text-white backdrop-blur-md"
						>
							<ArrowLeft class="size-5 rotate-180" />
						</Button>
					</Carousel.NextTrigger>
				</Carousel.Control>
			</div>
		</Carousel>
	</div>
</section>
