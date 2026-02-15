<script lang="ts">
	import { cn } from '$lib/utils.js';
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	import type { Snippet } from 'svelte';
	import { cubicIn, quintOut } from 'svelte/easing';
	import type { TransitionConfig } from 'svelte/transition';

	let {
		ref = $bindable(null),
		sideOffset = 4,
		portalProps,
		children,
		class: className,
		...restProps
	}: DropdownMenuPrimitive.ContentProps & {
		portalProps?: DropdownMenuPrimitive.PortalProps;
		children: Snippet;
	} = $props();

	interface ScaleFadeTransitionParams {
		delay?: number;
		duration?: number;
		easing?: (t: number) => number;
		from?: number;
	}

	function scaleFadeTransition(
		node: HTMLElement,
		{ delay = 0, duration = 200, easing = quintOut, from = 0.95 }: ScaleFadeTransitionParams = {}
	): TransitionConfig {
		// Detect where the menu is relative to the trigger
		const side = node.getAttribute('data-side') || 'bottom';
		const align = node.getAttribute('data-align') || 'center';

		// Map side/align to CSS transform-origin
		const originMap: Record<string, string> = {
			top: 'bottom',
			bottom: 'top',
			left: 'right',
			right: 'left'
		};

		const origin = `${originMap[side]} ${align === 'center' ? 'center' : align}`;

		return {
			delay,
			duration,
			easing,
			css: (t: number) => {
				const currentScale = from + (1 - from) * t;
				return `
                    opacity: ${t};
                    transform: scale(${currentScale});
                    transform-origin: ${origin};
                `;
			}
		};
	}
</script>

<DropdownMenuPrimitive.Portal {...portalProps}>
	<DropdownMenuPrimitive.Content
		bind:ref
		data-slot="dropdown-menu-content"
		{sideOffset}
		class={cn(
			'z-50 max-h-(--bits-dropdown-menu-content-available-height) min-w-40 overflow-x-hidden overflow-y-auto rounded-lg bg-white text-foreground shadow-sm shadow-black/10 outline-none',
			className
		)}
		{...restProps}
		forceMount={true}
	>
		{#snippet child({ wrapperProps, props, open })}
			{#if open}
				<div {...wrapperProps}>
					<div
						{...props}
						in:scaleFadeTransition|global={{ easing: quintOut, duration: 200 }}
						out:scaleFadeTransition|global={{ easing: cubicIn, duration: 150, from: 0.98 }}
					>
						{@render children?.()}
					</div>
				</div>
			{/if}
		{/snippet}
	</DropdownMenuPrimitive.Content>
</DropdownMenuPrimitive.Portal>
