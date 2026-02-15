<script lang="ts">
	import { Dialog as SheetPrimitive } from 'bits-ui';
	import { cn } from '$lib/utils.js';
	import { fade } from 'svelte/transition';

	let {
		ref = $bindable(null),
		class: className,
		...restProps
	}: SheetPrimitive.OverlayProps = $props();
</script>

<SheetPrimitive.Overlay
	bind:ref
	data-slot="sheet-overlay"
	class={cn('fixed inset-0 z-50 h-full w-full bg-black/70 backdrop-blur-sm', className)}
	{...restProps}
	forceMount
>
	{#snippet child({ props, open })}
		{#if open}
			<div {...props} transition:fade|global={{ duration: 300 }}></div>
		{/if}
	{/snippet}
</SheetPrimitive.Overlay>
