<script>
	import Input from '$lib/components/ui/input/input.svelte';
	import Content from '$lib/components/content.svelte';
	import Button from '$lib/components/ui/button/button.svelte';
</script>

<Content cutout paddingY={true} class="">
	<!-- <Input placeholder="ass is good" class="w-[20rem]" /> -->
	<div class="grid grid-cols-2">
		<div class="flex h-52 flex-col items-center justify-center space-y-10">
			<p>Primary buttons</p>
			<div class="grid w-full grid-cols-4 gap-4 p-4">
				<Button variant="primary">Primary</Button>
				<Button variant="primary-light">Primary light</Button>
				<Button variant="primary-ghost">Primary ghost</Button>
				<Button variant="primary-outline">Primary outline</Button>
			</div>
		</div>
		<div class="flex h-52 flex-col items-center justify-center space-y-10">
			<p>Secondary buttons</p>
			<div class="grid w-full grid-cols-4 gap-4 p-4">
				<Button variant="secondary">Secondary</Button>
				<Button variant="secondary-light">Secondary light</Button>
				<Button variant="secondary-ghost">Secondary ghost</Button>
				<Button variant="secondary-outline">Secondary outline</Button>
			</div>
		</div>
		<div class="flex h-52 flex-col items-center justify-center space-y-10">
			<p>success buttons</p>
			<div class="grid w-full grid-cols-4 gap-4 p-4">
				<Button variant="success">success</Button>
				<Button variant="success-light">success light</Button>
				<Button variant="success-ghost">success ghost</Button>
				<Button variant="success-outline">success outline</Button>
			</div>
		</div>
		<div class="flex h-52 flex-col items-center justify-center space-y-10">
			<p>destructive buttons</p>
			<div class="grid w-full grid-cols-4 gap-4 p-4">
				<Button variant="destructive">destructive</Button>
				<Button variant="destructive-light">destructive light</Button>
				<Button variant="destructive-ghost">destructive ghost</Button>
				<Button variant="destructive-outline">destructive outline</Button>
			</div>
		</div>
		<div class="flex h-52 flex-col items-center justify-center space-y-10">
			<p>ghost buttons</p>
			<div class="grid w-full grid-cols-4 gap-4 p-4">
				<Button variant="ghost">ghost</Button>
				<Button variant="ghost-ghost">ghost ghost</Button>
			</div>
		</div>
	</div>
</Content>
