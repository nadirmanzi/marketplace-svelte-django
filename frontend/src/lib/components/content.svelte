<script lang="ts">
	import { cn } from '$lib/utils';

	let {
		children,
		cutout = false,
		paddingX = false,
		paddingY = false,
		class: className,
		id = ''
	}: {
		children?: any;
		cutout?: boolean;
		paddingX?: boolean;
		paddingY?: boolean;
		class?: string;
		id?: string;
	} = $props();
</script>

<div
	class={cn(
		`${cutout ? 'absolute top-16 left-0 min-h-[calc(100vh-4rem)] ' : ''} @container w-full overflow-hidden bg-background ${paddingX ? `px-4` : ''} ${paddingY ? `py-4` : ''}`,
		className
	)}
	{id}
>
	{@render children?.()}
</div>
