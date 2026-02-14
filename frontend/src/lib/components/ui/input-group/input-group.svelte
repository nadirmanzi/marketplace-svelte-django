<script lang="ts">
	import { cn, type WithElementRef } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	let {
		ref = $bindable(null),
		class: className,
		children,
		...props
	}: WithElementRef<HTMLAttributes<HTMLDivElement>> = $props();
</script>

<div
	bind:this={ref}
	data-slot="input-group"
	role="group"
	class={cn(
		'group/input-group relative flex min-w-72 overflow-hidden items-center rounded-full border border-input-border bg-input-background transition-all outline-none',
		'h-9 has-[>textarea]:h-auto',

		// Variants based on alignment.
		'has-[>[data-align=inline-start]]:[&>input]:ps-2',
		'has-[>[data-align=inline-end]]:[&>input]:pe-2',
		'has-[>[data-align=block-start]]:h-auto has-[>[data-align=block-start]]:flex-col has-[>[data-align=block-start]]:[&>input]:pb-3',
		'has-[>[data-align=block-end]]:h-auto has-[>[data-align=block-end]]:flex-col has-[>[data-align=block-end]]:[&>input]:pt-3',

		// Focus state.
		'has-[[data-slot=input-group-control]:focus-visible]:ring-[1.5px] has-[[data-slot=input-group-control]:focus-visible]:ring-offset-1 has-[[data-slot=input-group-control]:focus-visible]:ring-offset-input-background has-[[data-slot=input-group-control]:focus-visible]:border-transparent has-[[data-slot=input-group-control]:focus-visible]:ring-input-ring',

		// Error state.
		'has-[[data-slot][aria-invalid=true]]:border-destructive has-[[data-slot][aria-invalid=true]]:ring-destructive/20 dark:has-[[data-slot][aria-invalid=true]]:ring-destructive/40',

		className
	)}
	{...props}
>
	{@render children?.()}
</div>
