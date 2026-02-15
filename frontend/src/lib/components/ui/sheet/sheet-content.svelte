<script lang="ts" module>
	import { tv, type VariantProps } from 'tailwind-variants';
	export const sheetVariants = tv({
		base: 'bg-white fixed z-50 flex flex-col shadow-lg overflow-y-auto',
		variants: {
			side: {
				top: 'inset-x-0 top-0 h-auto ',
				bottom: 'inset-x-0 bottom-0 h-auto ',
				left: 'inset-y-0 start-0 h-full w-3/4 sm:max-w-sm',
				right: 'inset-y-0 end-0 h-dvh min-w-1/3 '
			}
		},
		defaultVariants: {
			side: 'right'
		}
	});

	export type Side = VariantProps<typeof sheetVariants>['side'];
</script>

<script lang="ts">
	import { Dialog as SheetPrimitive } from 'bits-ui';
	import XIcon from '@lucide/svelte/icons/x';
	import { type Snippet } from 'svelte';
	import SheetOverlay from './sheet-overlay.svelte';
	import { cn, type WithoutChildrenOrChild } from '$lib/utils.js';
	import Button from '../button/button.svelte';
	import { expoOut, cubicIn } from 'svelte/easing';
	import type { TransitionConfig } from 'svelte/transition';

	let {
		ref = $bindable(null),
		class: className,
		side = 'right',
		portalProps,
		children,
		...restProps
	}: WithoutChildrenOrChild<SheetPrimitive.ContentProps> & {
		portalProps?: SheetPrimitive.PortalProps;
		side?: Side;
		children: Snippet;
	} = $props();

	function sheetTransition(node: HTMLElement): TransitionConfig {
		const isVertical = side === 'top' || side === 'bottom';
		const isNegative = side === 'top' || side === 'left';

		// Determine travel distance (100% of the element's own size)
		const offset = 100;

		return {
			duration: 500,
			easing: expoOut,
			css: (t) => {
				// In Svelte transitions, 't' is 0 -> 1 (entering)
				// We want to translate from 100% to 0%
				const translateValue = (1 - t) * (isNegative ? -offset : offset);
				const x = isVertical ? 0 : translateValue;
				const y = isVertical ? translateValue : 0;

				return `
                    transform: translate3d(${x}%, ${y}%, 0);
                    opacity: ${t};
                `;
			}
		};
	}
</script>

<SheetPrimitive.Portal {...portalProps}>
	<SheetOverlay />
	<SheetPrimitive.Content
		bind:ref
		data-slot="sheet-content"
		class={cn(sheetVariants({ side }), className)}
		{...restProps}
		forceMount={true}
	>
		{#snippet child({ props, open })}
			{#if open}
				<div {...props} transition:sheetTransition|global>
					{@render children?.()}
					<SheetPrimitive.Close class="absolute end-4 top-4">
						<Button variant="ghost-ghost" size="icon-sm" class="rounded-full">
							<XIcon class="size-4" strokeWidth={1.8} />
							<span class="sr-only">Close</span>
						</Button>
					</SheetPrimitive.Close>
				</div>
			{/if}
		{/snippet}
	</SheetPrimitive.Content>
</SheetPrimitive.Portal>
