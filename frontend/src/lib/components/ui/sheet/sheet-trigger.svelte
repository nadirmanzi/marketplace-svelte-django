<script lang="ts">
	import { Dialog as SheetPrimitive } from 'bits-ui';
	import {
		buttonVariants,
		type ButtonVariant,
		type ButtonSize
	} from '$lib/components/ui/button/index.js';
	import { cn } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		variant = 'primary',
		size = 'default',
		...restProps
	}: SheetPrimitive.TriggerProps & {
		variant?: ButtonVariant;
		size?: ButtonSize;
	} = $props();
</script>

<SheetPrimitive.Trigger
	bind:ref
	data-slot="sheet-trigger"
	class={cn(buttonVariants({ variant, size }), className)}
	{...restProps}
/>
