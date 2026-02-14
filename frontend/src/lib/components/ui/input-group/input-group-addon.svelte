<script lang="ts" module>
	import { tv, type VariantProps } from 'tailwind-variants';
	export const inputGroupAddonVariants = tv({
		base: "text-foreground bg-ghost relative flex h-full px-2 w-auto min-w-8 flex-initial cursor-text select-none items-center justify-center gap-2 text-sm font-medium group-data-[disabled=true]/input-group:opacity-50",
		variants: {
			align: {
				'inline-start':
					'order-first',
				'inline-end': 'order-last ',
				'block-start':
					'[.border-b]:pb-3 order-first w-full justify-start px-3 pt-3 group-has-[>input]/input-group:pt-2.5',
				'block-end':
					'[.border-t]:pt-3 order-last w-full justify-start px-3 pb-3 group-has-[>input]/input-group:pb-2.5'
			}
		},
		defaultVariants: {
			align: 'inline-start'
		}
	});

	export type InputGroupAddonAlign = VariantProps<typeof inputGroupAddonVariants>['align'];
</script>

<script lang="ts">
	import { cn, type WithElementRef } from '$lib/utils.js';
	import type { HTMLAttributes } from 'svelte/elements';

	let {
		ref = $bindable(null),
		class: className,
		children,
		align = 'inline-start',
		...restProps
	}: WithElementRef<HTMLAttributes<HTMLDivElement>> & {
		align?: InputGroupAddonAlign;
	} = $props();
</script>

<div
	bind:this={ref}
	role="group"
	data-slot="input-group-addon"
	data-align={align}
	class={cn(inputGroupAddonVariants({ align }), '', className)}
	onclick={(e) => {
		if ((e.target as HTMLElement).closest('button')) {
			return;
		}
		e.currentTarget.parentElement?.querySelector('input')?.focus();
	}}
	{...restProps}
>
	<div class="flex items-center justify-center gap-2">
		{@render children?.()}
	</div>
</div>
