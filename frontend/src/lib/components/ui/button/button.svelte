<script lang="ts" module>
	import { cn, type WithElementRef } from '$lib/utils.js';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';
	import { type VariantProps, tv } from 'tailwind-variants';

	export const buttonVariants = tv({
		base: "aria-invalid:ring-destructive/20 cursor-pointer aria-invalid:border-destructive inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm outline-none transition-all disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0",
		variants: {
			variant: {
				primary:
					'bg-primary text-primary-foreground hover:bg-primary-hover active:bg-primary-active',
				secondary:
					'bg-secondary text-secondary-foreground hover:bg-secondary-hover active:bg-secondary-active',
				ghost: 'bg-transparent text-foreground hover:bg-ghost active:bg-ghost-active',
				'ghost-secondary':
					'bg-transparent text-foreground hover:bg-ghost-secondary active:bg-ghost-secondary-active',
				outline:
					'border border-border text-foreground bg-transparent hover:bg-ghost active:bg-ghost-active',
				'outline-secondary':
					'border border-border-secondary bg-transparent hover:bg-ghost-secondary active:bg-ghost-secondary-active',
				destructive:
					'bg-destructive text-destructive-foreground hover:bg-destructive-hover active:bg-destructive-active',
				success:
					'bg-success text-success-foreground hover:bg-success-hover active:bg-success-active'
			},
			size: {
				lg: 'h-10 px-4 gap-2.5',
				default: 'h-9 px-4 gap-2.5',
				sm: 'h-8 px-4 gap-2.5',
				icon: 'h-9 w-9',
				'icon-lg': 'h-10 w-10',
				'icon-sm': 'h-8 w-8',
				'icon-xs': 'h-7 w-7',
			}
		},
		defaultVariants: {
			variant: 'primary',
			size: 'default'
		}
	});

	export type ButtonVariant = VariantProps<typeof buttonVariants>['variant'];
	export type ButtonSize = VariantProps<typeof buttonVariants>['size'];

	export type ButtonProps = WithElementRef<HTMLButtonAttributes> &
		WithElementRef<HTMLAnchorAttributes> & {
			variant?: ButtonVariant;
			size?: ButtonSize;
		};
</script>

<script lang="ts">
	let {
		class: className,
		variant = 'primary',
		size = 'default',
		ref = $bindable(null),
		href = undefined,
		type = 'button',
		disabled,
		children,
		...restProps
	}: ButtonProps = $props();
</script>

{#if href}
	<a
		bind:this={ref}
		data-slot="button"
		class={cn(buttonVariants({ variant, size }), className)}
		href={disabled ? undefined : href}
		aria-disabled={disabled}
		role={disabled ? 'link' : undefined}
		tabindex={disabled ? -1 : undefined}
		{...restProps}
	>
		{@render children?.()}
	</a>
{:else}
	<button
		bind:this={ref}
		data-slot="button"
		class={cn(buttonVariants({ variant, size }), className)}
		{type}
		{disabled}
		{...restProps}
	>
		{@render children?.()}
	</button>
{/if}
