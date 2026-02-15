<script lang="ts">
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		User,
		ChevronRight,
		UserPlus,
		Menu,
		LogIn,
		HeartHandshake,
		FileQuestionMark,
		LifeBuoy
	} from '@lucide/svelte';
	import { fade } from 'svelte/transition';

	const MENU_ITEMS = [
		{
			href: '/auth/login',
			label: 'Log in',
			icon: LogIn
		},
		{
			href: '/auth/register',
			label: 'Register',
			icon: UserPlus
		},
		{
			href: '/help-center',
			label: 'Help center',
			icon: LifeBuoy
		},
		{
			href: '/auth/register/seller',
			label: 'Become a seller',
			icon: HeartHandshake
		}
	];
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger variant="ghost-ghost" size="icon">
		<Menu class="size-4" strokeWidth={1.8} />
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end" alignOffset={8} side="bottom" sideOffset={16} class="w-50">
		<DropdownMenu.Group>
			{#each MENU_ITEMS as item}
				{@const Icon = item.icon}
				<a href={item.href}>
					<DropdownMenu.Item
						class={`${item.href === '/auth/register/seller' ? 'bg-primary-light text-primary data-highlighted:bg-primary-light-hover data-highlighted:text-primary' : ''}`}
					>
						<Icon
							class={`${item.href === '/auth/register/seller' ? 'text-primary' : ''} order-first size-4`}
							strokeWidth={1.8}
						/>

						<p class="text-sm">{item.label}</p>
					</DropdownMenu.Item>
				</a>
			{/each}
		</DropdownMenu.Group>
	</DropdownMenu.Content>
</DropdownMenu.Root>
