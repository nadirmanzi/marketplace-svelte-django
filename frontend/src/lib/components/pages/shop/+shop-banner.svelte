<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import { Carousel } from '@skeletonlabs/skeleton-svelte';
	import ArrowLeft from '@tabler/icons-svelte-runes/icons/arrow-left';
	import Shoes from '$lib/assets/shoes.jpg';
	import Clothes from '$lib/assets/clothes.jpg';
	import Furniture from '$lib/assets/furniture.jpg';
	import Electronics from '$lib/assets/electronics.jpg';
	import Cosmetics from '$lib/assets/cosmetics.jpg';
	import Sports from '$lib/assets/sports.jpg';
	import { fly, slide } from 'svelte/transition';
	import {
		bounceIn,
		bounceInOut,
		bounceOut,
		expoIn,
		expoInOut,
		expoOut,
		quintIn,
		quintInOut
	} from 'svelte/easing';

	const slides = $state([
		{ image: Shoes, title: 'Shoes', href: '' },
		{ image: Clothes, title: 'Clothes', href: '' },
		{ image: Furniture, title: 'Furniture', href: '' },
		{ image: Electronics, title: 'Electronics', href: '' },
		{ image: Cosmetics, title: 'Cosmetics', href: '' },
		{ image: Sports, title: 'Sports', href: '' }
	]);

	let heading = $state('Everything You Need, All in One Place');
</script>

<section class="flex h-full flex-col justify-evenly space-y-20 p-8">
	<div class="mx-auto flex max-w-3xl flex-col space-y-2 text-center">
		<p class="font-semibold text-secondary">Discover. Buy. Experience</p>
		<div class="space-y-10">
			<div class="flex space-x-2">
				<p class="font-display text-4xl font-extrabold">
					{heading}
				</p>
			</div>
			<p class="mx-auto max-w-xl text-surface-foreground-muted">
				Skip the search. Our curated collections make it easy to find quality products all in one
				seamless experience
			</p>
		</div>
	</div>

	<div class="flex w-full">
		<Carousel
			slideCount={slides.length}
			slidesPerPage={5}
			loop
			allowMouseDrag
			snapType={'mandatory'}
			slidesPerMove={1}
			spacing={'1.5rem'}
			autoplay={{ delay: 3000 }}
			class="relative mx-auto flex max-w-[95%] flex-col"
		>
			<Carousel.ItemGroup class="h-full w-full">
				{#each slides as slide, i (i)}
					<Carousel.Item
						index={i}
						class="group h-full flex-col items-center space-y-2 overflow-hidden rounded-lg "
					>
						<a href={slide.href} class="block h-[20rem] overflow-hidden rounded-2xl">
							<img
								src={slide.image ?? ''}
								class="block h-full w-full bg-center object-cover transition-transform duration-300 ease-in-out group-hover:scale-105"
								alt=""
							/>
						</a>
						<p class="w-full text-center text-lg font-semibold">
							{slide.title}
						</p>
					</Carousel.Item>
				{/each}
			</Carousel.ItemGroup>

			<div class="absolute -top-14 right-0 z-20">
				<Carousel.Control class="flex items-center gap-4">
					<Carousel.PrevTrigger>
						<Button variant="outline" class="border-none bg-nav-bg text-white hover:bg-nav-bg/80">
							<ArrowLeft class="size-5" />
						</Button>
					</Carousel.PrevTrigger>
					<Carousel.NextTrigger>
						<Button variant="outline" class="border-none bg-nav-bg text-white hover:bg-nav-bg/80">
							<ArrowLeft class="size-5 rotate-180" />
						</Button>
					</Carousel.NextTrigger>
				</Carousel.Control>
			</div>
		</Carousel>
	</div>
</section>
