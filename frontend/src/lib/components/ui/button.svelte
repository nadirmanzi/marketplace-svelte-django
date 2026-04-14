<script lang="ts">
	import { tv, type VariantProps } from 'tailwind-variants';
	import { cn } from '$lib/utils';
	import type { HTMLButtonAttributes, HTMLAnchorAttributes } from 'svelte/elements';

	export const buttonVariants = tv({
		base: 'relative min-w-0 inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-semibold overflow-hidden select-none transition-all duration-200 ease-out focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97] active:duration-75',

		variants: {
			color: {
				primary: '',
				secondary: '',
				destructive: '',
				success: '',
				black: 'bg-nav-bg text-white hover:bg-nav-bg/90 active:bg-nav-bg/90'
			},
			variant: {
				filled: '',
				tonal: '',
				outline: 'border-2 bg-transparent',
				ghost: 'bg-transparent'
			},
			size: {
				sm: 'h-8 px-3 py-1 text-xs gap-1.5 min-w-16 [&_svg]:size-3.5',
				md: 'h-9.5 px-4 py-2 text-sm gap-2 min-w-20 [&_svg]:size-4.5',
				lg: 'h-11 px-5 py-3 text-base gap-2.5 min-w-24 [&_svg]:size-5.5',
				icon: 'size-10 [&_svg]:size-5'
			}
		},

		compoundVariants: [
			// PRIMARY FILLED
			{
				color: 'primary',
				variant: 'filled',
				class: 'bg-primary text-on-primary hover:bg-primary-hover active:bg-primary-hover'
			},
			// PRIMARY TONAL
			{
				color: 'primary',
				variant: 'tonal',
				class:
					'bg-primary-tonal text-on-primary-tonal hover:bg-primary-tonal-hover active:bg-primary-tonal-hover'
			},
			// PRIMARY OUTLINE
			{
				color: 'primary',
				variant: 'outline',
				class: 'border-primary/70 text-primary hover:bg-primary-tonal/50 '
			},

			// SECONDARY FILLED
			{
				color: 'secondary',
				variant: 'filled',
				class: 'bg-secondary text-on-secondary hover:bg-secondary-hover active:bg-secondary-hover'
			},
			// SECONDARY TONAL
			{
				color: 'secondary',
				variant: 'tonal',
				class:
					'bg-secondary-tonal text-on-secondary-tonal hover:bg-secondary-tonal-hover active:bg-secondary-tonal-hover'
			},
			// SECONDARY OUTLINE
			{
				color: 'secondary',
				variant: 'outline',
				class: 'border-secondary/70 text-secondary hover:bg-secondary-tonal/50 '
			},

			// DESTRUCTIVE FILLED
			{
				color: 'destructive',
				variant: 'filled',
				class:
					'bg-destructive text-on-destructive hover:bg-destructive-hover active:bg-destructive-hover'
			},
			// DESTRUCTIVE TONAL
			{
				color: 'destructive',
				variant: 'tonal',
				class:
					'bg-destructive-tonal text-on-destructive-tonal hover:bg-destructive-tonal-hover active:bg-destructive-tonal-hover'
			},
			// DESTRUCTIVE OUTLINE
			{
				color: 'destructive',
				variant: 'outline',
				class: 'border-destructive/70 text-destructive hover:bg-destructive-tonal/50 '
			},

			// SUCCESS FILLED
			{
				color: 'success',
				variant: 'filled',
				class: 'bg-success text-on-success hover:bg-success-hover active:bg-success-hover'
			},
			// SUCCESS TONAL
			{
				color: 'success',
				variant: 'tonal',
				class:
					'bg-success-tonal text-on-success-tonal hover:bg-success-tonal-hover active:bg-success-tonal-hover'
			},
			// SUCCESS OUTLINE
			{
				color: 'success',
				variant: 'outline',
				class: 'border-success/70 text-success hover:bg-success-tonal/50 '
			},

			// BLACK
			{
				color: 'black',
				variant: 'filled',
				class: 'bg-nav-bg text-white hover:bg-nav-bg/90 active:bg-nav-bg/90'
			},
			{
				color: 'black',
				variant: 'tonal',
				class: 'bg-nav-bg/10 text-white hover:bg-nav-bg/20 active:bg-nav-bg/20'
			},
			{
				color: 'black',
				variant: 'outline',
				class: 'border-nav-bg/70 text-nav-bg hover:bg-nav-bg/10 '
			},
			{
				color: 'black',
				variant: 'ghost',
				class: 'text-nav-bg'
			},

			// GHOST — transparent bg, text color only, ripple on click
			{ color: 'primary', variant: 'ghost', class: 'text-primary' },
			{ color: 'secondary', variant: 'ghost', class: 'text-secondary' },
			{ color: 'destructive', variant: 'ghost', class: 'text-destructive' },
			{ color: 'success', variant: 'ghost', class: 'text-success' }
		],

		defaultVariants: {
			color: 'primary',
			variant: 'filled',
			size: 'md'
		}
	});

	type ButtonVariantProps = VariantProps<typeof buttonVariants>;

	interface Ripple {
		id: number;
		x: number;
		y: number;
		size: number;
	}

	type Props = ButtonVariantProps &
		HTMLButtonAttributes &
		HTMLAnchorAttributes & {
			children?: import('svelte').Snippet;
			rippleDuration?: number;
		};

	let {
		children,
		color = 'primary',
		variant = 'filled',
		size,
		href,
		type = 'button',
		onclick,
		rippleDuration = 1200,
		class: className,
		...rest
	}: Props = $props();

	const classes = $derived(cn(buttonVariants({ color, variant, size }), className));

	// --- Ripple effect ---
	let ripples: Ripple[] = $state([]);
	let rippleId = 0;

	function getRippleColor(): string {
		if (variant === 'filled') {
			return 'rgba(255, 255, 255, 0.35)';
		}
		const rippleColors: Record<string, string> = {
			primary: 'oklch(22% 0 0 / 0.12)',
			secondary: 'oklch(58% 0.22 45 / 0.15)',
			destructive: 'oklch(45% 0.24 27 / 0.15)',
			success: 'oklch(48% 0.18 155 / 0.15)'
		};
		return rippleColors[color ?? 'primary'] ?? rippleColors.primary;
	}

	function handlePointerDown(e: PointerEvent) {
		const target = e.currentTarget as HTMLElement;
		const rect = target.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;
		const size = Math.max(rect.width, rect.height) * 2.5;

		ripples = [...ripples, { id: rippleId++, x, y, size }];
	}

	function removeRipple(id: number) {
		ripples = ripples.filter((r) => r.id !== id);
	}
</script>

{#snippet rippleLayer()}
	{#each ripples as ripple (ripple.id)}
		<span
			class="ripple-circle"
			style="
                --ripple-duration: {rippleDuration}ms;
                left: {ripple.x}px;
                top: {ripple.y}px;
                width: {ripple.size}px;
                height: {ripple.size}px;
                background: {getRippleColor()};
            "
			onanimationend={() => removeRipple(ripple.id)}
		></span>
	{/each}
{/snippet}

{#if href}
	<a {href} class={classes} onpointerdown={handlePointerDown} {...rest as HTMLAnchorAttributes}>
		{@render rippleLayer()}
		<span class="relative z-1 inline-flex items-center gap-[inherit]">
			{@render children?.()}
		</span>
	</a>
{:else}
	<button
		{type}
		{onclick}
		class={classes}
		onpointerdown={handlePointerDown}
		{...rest as HTMLButtonAttributes}
	>
		{@render rippleLayer()}
		<span class="relative z-1 inline-flex items-center gap-[inherit]">
			{@render children?.()}
		</span>
	</button>
{/if}

<style>
	.ripple-circle {
		position: absolute;
		border-radius: 50%;
		transform: translate(-50%, -50%) scale(0);
		animation: ripple-expand var(--ripple-duration, 600ms) cubic-bezier(0.2, 0, 0, 1) forwards;
		pointer-events: none;
		z-index: 0;
	}

	@keyframes ripple-expand {
		0% {
			transform: translate(-50%, -50%) scale(0);
			opacity: 1;
		}
		100% {
			transform: translate(-50%, -50%) scale(1);
			opacity: 0;
		}
	}
</style>
