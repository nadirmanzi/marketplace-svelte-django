<script>
	import Input from '$lib/components/ui/input/input.svelte';
	import banner from '$lib/assets/banner3.jpg';
	import { onMount } from 'svelte';
	import gsap from 'gsap';
	import { ScrollTrigger } from 'gsap/ScrollTrigger';
	import { ScrollSmoother } from 'gsap/ScrollSmoother';
	import Content from '$lib/components/content.svelte';

	onMount(() => {
		gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

		let ctx = gsap.context(() => {
			gsap.to('#banner-container', {
				scrollTrigger: {
					trigger: '#banner-container',
					// scroller: 'main',
					start: 'top top',
					end: '+=50%',
					scrub: 1,
					markers: true
					// pin: '#banner-container'
				},
				scale: 0.8,
				borderRadius: '0.5rem',
				opacity: 0
			});
		});

		return () => ctx.revert();
	});
</script>

<svelte:head>
	<title>Home - Marketplace</title>
</svelte:head>

<Content class="h-dvh" id="banner-container">
	<img id="banner" src={banner} alt="Banner" class="h-full w-full object-cover" />
</Content>

<Content>
	<p>adadsad</p>
	<p>adadsad</p>
	<p>adadsad</p>
	<p>adadsad</p>
	<p>adadsad</p>
	<p>adadsad</p>
</Content>
