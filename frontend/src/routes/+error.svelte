<script lang="ts">
	import Logo from '$lib/components/logo.svelte';
	import NavLink from '$lib/components/navigation/nav-link.svelte';
	import { HeartCrack, House, Search } from '@lucide/svelte';
	import * as InputGroup from '$lib/components/ui/input-group/index';
	import NavMenuDropdown from '$lib/components/navigation/nav-menu-dropdown.svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import gsap from 'gsap';
	import { onMount } from 'svelte';
	import TopNavigation from '$lib/components/navigation/top-navigation.svelte';
	import Content from '$lib/components/content.svelte';

	const NAVIGATION_LINKS = [
		{ href: '/browse', label: 'Browse' },
		{ href: '/categories', label: 'Categories' },
		{ href: '/verified-vendors', label: 'Verified vendors' },
		{ href: '/track-order', label: 'Track order' }
	];

	onMount(() => {
		// 1. Setup the Infinite Heartbeat/Color Animation
		const heartbeat = gsap.fromTo(
			'#heart-crack',
			{
				repeatRefresh: true // Ensures CSS variables re-evaluate
			},
			{
				rotate: 10,
				scale: 0.95,
				repeat: -1,
				yoyo: true,
				yoyoEase: 'elastic.out(1, 0.3)',
				repeatRefresh: true, // Ensures CSS variables re-evaluate
				duration: 1.5
			}
		);

		// 2. Setup High-Performance Mouse Follower
		// quickTo is much faster than standard tweens for mouse tracking
		const xTo = gsap.quickTo('#heart-crack', 'x', { duration: 0.6, ease: 'power3' });
		const yTo = gsap.quickTo('#heart-crack', 'y', { duration: 0.6, ease: 'power3' });

		const handleMouseMove = (e: MouseEvent) => {
			const xPos = (e.clientX / window.innerWidth - 0.5) * 30;
			const yPos = (e.clientY / window.innerHeight - 0.5) * 30;

			xTo(xPos);
			yTo(yPos);
		};

		window.addEventListener('mousemove', handleMouseMove);

		return () => {
			window.removeEventListener('mousemove', handleMouseMove);
			heartbeat.kill();
		};
	});
</script>

<svelte:head>
	<title>404 - page not found</title>
</svelte:head>

<TopNavigation>
	<div>
		{#each NAVIGATION_LINKS as { href, label }}
			<NavLink {href} {label}></NavLink>
		{/each}
	</div>

	<div>
		<NavMenuDropdown />
	</div>
</TopNavigation>

<Content class="min-h-dvh">
	<div
		class="absolute top-1/2 left-1/2 flex w-full -translate-x-1/2 -translate-y-1/2 items-center justify-evenly"
	>
		<div class="space-y-8 text-center">
			<div class="">
				<h1 class="text-[2rem]">OOPS !</h1>
				<p class="text-foreground-secondary">The page you are looking for can't be found.</p>
			</div>

			<div class="flex flex-col items-center space-y-4">
				<InputGroup.Root class="w-full">
					<InputGroup.Input placeholder="Search for something" />
					<InputGroup.Addon align="inline-start">
						<Search class="size-4" strokeWidth={1.8} />
					</InputGroup.Addon>
				</InputGroup.Root>
				<p>or</p>
				<Button variant="secondary" href="/" class="" aria-label="Return to the homepage">
					<House strokeWidth={1.8} class="size-4" />
					<p>Go back home</p>
				</Button>
			</div>
		</div>
		<div
			class="flex items-center justify-center space-x-4 text-[15rem] leading-50 font-extrabold select-none"
		>
			<p id="four-1" class="text-foreground-secondary/30">4</p>
			<HeartCrack id="heart-crack" class="size-40 text-destructive" />
			<p id="four-2" class="text-foreground-secondary/30">4</p>
		</div>
	</div>
</Content>
