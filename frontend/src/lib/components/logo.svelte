<script lang="ts">
	import primaryLogo from '$lib/assets/primary-logo.svg';
	import darkLogo from '$lib/assets/dark-logo.svg';
	import lightLogo from '$lib/assets/light-logo.svg';
	import { cn } from '$lib/utils';

	let {
		variant = 'primary',
		class: className = ''
	}: { variant?: 'primary' | 'dark' | 'light'; class?: string } = $props();
</script>

<a href="/">
	<enhanced:img
		src={variant === 'primary' ? primaryLogo : variant === 'dark' ? darkLogo : lightLogo}
		alt="[marketplace] Logo"
		fetchpriority="high"
		class={cn('size-8', className)}
	/>
</a>
