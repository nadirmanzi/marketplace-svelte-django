<script lang="ts" module>
	/*
	 * ─── INPUT COMPONENT (SHARED UI) ─────────────────────────────────────────────
	 * A highly flexible, context-aware input component.
	 * Supports various surfaces (standard background, card surfaces, or dark navigation).
	 * Built with tailwind-variants for robust state and style management.
	 * ───────────────────────────────────────────────────────────────────────────────
	 */
	import { tv, type VariantProps } from 'tailwind-variants';

	/** Input Design System Definition */
	export const inputVariants = tv({
		slots: {
			root: 'group relative flex w-full flex-col gap-2',
			// Rounded pill by default with smooth ease-out transitions
			wrapper:
				'relative flex w-full items-center overflow-hidden rounded-full border transition-all duration-200 ease-out',
			field:
				'peer w-full flex-1 bg-transparent text-sm text-foreground focus:outline-none disabled:cursor-not-allowed placeholder:text-foreground/50',
			label:
				'font-display font-medium text-sm group-focus-within:font-medium tracking-wide text-foreground transition-all duration-200 group-focus-within:text-foreground',
			leadingSlot: 'flex shrink-0 items-center justify-center text-foreground/50',
			trailingSlot: 'flex shrink-0 items-center justify-center text-foreground/50',
			helperText: 'text-[11px] leading-tight text-foreground/50',
			errorText: 'text-sm leading-tight font-medium text-destructive'
		},

		variants: {
			context: {
				// Grey Page Background
				background: {
					wrapper:
						'bg-surface border-[1.5px] border-foreground/15 hover:bg-background focus-within:bg-background focus-within:border-foreground/40'
				},
				// White Card / Content Surface
				surface: {
					wrapper:
						'bg-background border-[1.5px] hover:bg-surface focus-within:bg-surface border-foreground/20 ring-2 ring-transparent focus-within:ring-primary/20 focus-within:border-primary/40'
				},
				// Navigation Bar (Translucent / Dark)
				dark: {
					wrapper:
						'bg-white/10! border-1 border-white/30! rounded-full hover:bg-white/15! focus-within:bg-white/15! focus-within:border-nav-foreground/20!',
					field: 'text-nav-foreground placeholder:text-nav-foreground/60',
					label: 'text-nav-foreground/60 group-focus-within:text-nav-foreground',
					leadingSlot: 'text-nav-foreground',
					trailingSlot: 'text-nav-foreground/50',
					helperText: 'text-nav-foreground/50'
				}
			},
			size: {
				sm: {
					wrapper: 'h-8 px-3 gap-2',
					field: 'text-xs',
					leadingSlot: '[&_svg]:size-3.5',
					trailingSlot: '[&_svg]:size-3.5'
				},
				md: {
					wrapper: 'h-10 px-3.5 gap-2.5',
					field: 'text-sm',
					leadingSlot: '[&_svg]:size-4',
					trailingSlot: '[&_svg]:size-4'
				},
				lg: {
					wrapper: 'h-12 px-4 gap-3',
					field: 'text-base',
					leadingSlot: '[&_svg]:size-5',
					trailingSlot: '[&_svg]:size-5'
				}
			},
			state: {
				default: {},
				error: {
					wrapper:
						'!ring-2 !ring-destructive/20 focus-within:!ring-destructive/20 !border-destructive/60'
				},
				success: {
					wrapper: '!ring-2 !ring-success/20 focus-within:!ring-success/20 !border-success/60'
				},
				disabled: { wrapper: 'cursor-not-allowed opacity-50' }
			}
		},

		defaultVariants: {
			context: 'background',
			size: 'md',
			state: 'default'
		}
	});

	export type InputVariantProps = VariantProps<typeof inputVariants>;
</script>

<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLInputAttributes } from 'svelte/elements';
	import type { Snippet } from 'svelte';

	interface Props extends Omit<HTMLInputAttributes, 'size'> {
		context?: InputVariantProps['context'];
		size?: InputVariantProps['size'];
		error?: string | null;
		success?: boolean;
		label?: string;
		helperText?: string;
		leading?: Snippet;
		trailing?: Snippet;
		clearable?: boolean;
		class?: string;
		value?: HTMLInputAttributes['value'];
	}

	let {
		context = 'background',
		size = 'md',
		error = null,
		success = false,
		label,
		helperText,
		leading,
		trailing,
		disabled = false,
		class: className,
		id,
		value = $bindable(),
		...rest
	}: Props = $props();

	// ─── DOM REFERENCES ─────────────────────────────────────────────────────────
	let inputEl = $state<HTMLInputElement | null>(null);
	const inputId = $derived(id ?? `input-${crypto.randomUUID().slice(0, 8)}`);

	// ─── DERIVED STATES ─────────────────────────────────────────────────────────
	const inputState = $derived(
		disabled ? 'disabled' : error ? 'error' : success ? 'success' : 'default'
	);
	const slots = $derived(inputVariants({ context, size, state: inputState }));

	// ─── EFFECTS ────────────────────────────────────────────────────────────────
	$effect(() => {
		// Programmatic autofocus to bypass browser limitations during JS transitions
		if (rest.autofocus && inputEl) {
			inputEl.focus();
		}
	});
</script>

<div class={slots.root()}>
	{#if label}
		<label for={inputId} class={slots.label()}>{label}</label>
	{/if}

	<div class={cn(slots.wrapper(), className)}>
		<!-- Leading Context (Icons, etc) -->
		{#if leading}
			<span class={slots.leadingSlot()}>
				{@render leading()}
			</span>
		{/if}

		<input
			bind:this={inputEl}
			id={inputId}
			bind:value
			class={slots.field()}
			{disabled}
			aria-invalid={!!error}
			aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
			{...rest}
		/>

		<!-- Trailing Context / Clear Interaction -->
		{#if trailing}
			<span class={slots.trailingSlot()}>
				{@render trailing()}
			</span>
		{/if}
	</div>

	<!-- Messaging: Errors or Hints -->
	{#if error}
		<p id="{inputId}-error" class={slots.errorText()}>{error}</p>
	{:else if helperText}
		<p id="{inputId}-helper" class={slots.helperText()}>{helperText}</p>
	{/if}
</div>
