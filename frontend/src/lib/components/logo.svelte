<script lang="ts">
	import blackLogo from '$lib/assets/black-logo.svg';
	import whiteLogo from '$lib/assets/white-logo.svg';
	import { cn } from '$lib/utils';

	type LogoProps = {
		color?: 'black' | 'white';
		class?: string;
	};

	let { color, class: className }: LogoProps = $props();
</script>

<img src={color === 'black' ? blackLogo : whiteLogo} alt="" class={cn(className)} />
