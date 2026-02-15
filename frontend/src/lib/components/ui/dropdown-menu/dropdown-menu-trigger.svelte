<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
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
	}: DropdownMenuPrimitive.TriggerProps & {
		variant?: ButtonVariant;
		size?: ButtonSize;
	} = $props();
</script>

<DropdownMenuPrimitive.Trigger
	bind:ref
	data-slot="dropdown-menu-trigger"
	class={cn(buttonVariants({ variant, size }), className)}
	{...restProps}
/>
