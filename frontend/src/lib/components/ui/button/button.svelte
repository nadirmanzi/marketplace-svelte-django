<script lang="ts" module>
	import { cn, type WithElementRef } from '$lib/utils.js';
	import type { HTMLAnchorAttributes, HTMLButtonAttributes } from 'svelte/elements';
	import { type VariantProps, tv } from 'tailwind-variants';

	export const buttonVariants = tv({
		base: "aria-invalid:ring-destructive/20 cursor-pointer aria-invalid:border-destructive inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm outline-none transition-all disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0",
		variants: {
			variant: {
				// PRIMARY
				primary:
					'bg-primary text-primary-foreground hover:bg-primary-hover active:bg-primary-active',
				'primary-light':
					'bg-primary-light text-primary hover:bg-primary-light-hover active:bg-primary-light-active',
				'primary-ghost':
					'bg-transparent text-primary hover:bg-primary-light active:bg-primary-light-hover',
				'primary-outline':
					'border border-primary/30 text-primary bg-primary-light hover:bg-primary-light-hover active:bg-primary-light-active',

				// SECONDARY
				secondary:
					'bg-secondary text-secondary-foreground hover:bg-secondary-hover active:bg-secondary-active',
				'secondary-light':
					'bg-secondary-light text-secondary hover:bg-secondary-light-hover active:bg-secondary-light-active',
				'secondary-ghost':
					'bg-transparent text-secondary hover:bg-secondary/20 active:bg-secondary/30',
				'secondary-outline':
					'border border-secondary/50 text-secondary bg-secondary/20 hover:bg-secondary/30 active:bg-secondary/40',

				// SUCCESS
				success:
					'bg-success text-success-foreground hover:bg-success-hover active:bg-success-active',
				'success-light':
					'bg-success-light text-success hover:bg-success-light-hover active:bg-success-light-active',
				'success-ghost': 'bg-transparent text-success hover:bg-success/20 active:bg-success/30',
				'success-outline':
					'border border-success/50 text-success bg-success/20 hover:bg-success/30 active:bg-success/40',

				// DESTRUCTIVE
				destructive:
					'bg-destructive text-destructive-foreground hover:bg-destructive-hover active:bg-destructive-active',
				'destructive-light':
					'bg-destructive-light text-destructive hover:bg-destructive-light-hover active:bg-destructive-light-active',
				'destructive-ghost':
					'bg-transparent text-destructive hover:bg-destructive/20 active:bg-destructive/30',
				'destructive-outline':
					'border border-destructive/50 text-destructive bg-destructive/20 hover:bg-destructive/30 active:bg-destructive/40',

				// GHOST
				ghost: 'bg-ghost text-ghost-foreground hover:bg-ghost-hover active:bg-ghost-active',
				'ghost-ghost': 'bg-transparent text-foreground hover:bg-ghost active:bg-ghost-hover'
			},
			size: {
				lg: 'h-9.5 px-3.5 gap-2.5',
				default: 'h-8.5 px-3.5 gap-2',
				sm: 'h-7.5 px-3.5 gap-1.5',
				icon: 'h-9 w-9',
				'icon-lg': 'h-10 w-10',
				'icon-sm': 'h-8 w-8',
				'icon-xs': 'h-7 w-7'
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
