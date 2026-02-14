<script lang="ts">
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { User, ChevronRight, UserPlus, LogIn, HeartHandshake } from '@lucide/svelte';
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		<Button variant="ghost" size="icon">
			<User class="size-4" strokeWidth={1.8} />
		</Button>
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end" sideOffset={14} class="w-50">
		<DropdownMenu.Group>
			<a href="/auth/login">
				<DropdownMenu.Item class="p-3">
					<LogIn class="order-first size-4 " strokeWidth={1.8} />

					<div>
						<p class="text-sm">Log in</p>
						<!-- <p class="font- text-sm text-foreground-secondary">with an existing account</p> -->
					</div>
				</DropdownMenu.Item>
			</a>
			<a href="/auth/register">
				<DropdownMenu.Item class="p-3">
					<UserPlus class="order-first size-4 " strokeWidth={1.8} />

					<div>
						<p class="text-sm">Register</p>
						<!-- <p class="font- text-sm text-foreground-secondary">with an existing account</p> -->
					</div>
				</DropdownMenu.Item>
			</a>
			<a href="/auth/register/seller">
				<DropdownMenu.Item
					class="bg-primary/10 p-3 text-primary data-highlighted:bg-primary/20 data-highlighted:text-primary"
				>
					<HeartHandshake class="order-first size-4 text-primary" strokeWidth={1.8} />

					<div>
						<p class="text-sm">Become a seller</p>
						<!-- <p class="font- text-sm text-foreground-secondary">with an existing account</p> -->
					</div>
				</DropdownMenu.Item>
			</a>
		</DropdownMenu.Group>
	</DropdownMenu.Content>
</DropdownMenu.Root>
