<script lang="ts">
	import Button from '../ui/button.svelte';
	import type { Snippet } from 'svelte';
	import { slideFade } from './transitions.svelte';

	import Package from '@tabler/icons-svelte-runes/icons/package';
	import Receipt from '@tabler/icons-svelte-runes/icons/receipt';
	import Exchange from '@tabler/icons-svelte-runes/icons/exchange';
	import Heart from '@tabler/icons-svelte-runes/icons/heart';
	import User from '@tabler/icons-svelte-runes/icons/user';
	import ShieldLock from '@tabler/icons-svelte-runes/icons/shield-lock';
	import CreditCard from '@tabler/icons-svelte-runes/icons/credit-card';
	import BellRinging from '@tabler/icons-svelte-runes/icons/bell-ringing';

	let {
		onHover,
		isCrossHover,
		activeLabel
	}: {
		onHover: (link: any) => void;
		isCrossHover: boolean;
		activeLabel?: string;
	} = $props();
</script>

<!-- ─── NAV CONTENT SNIPPETS (The "Empty Canvas") ─── -->

<!-- Generic Snippet for Columns -->
{#snippet ListColumn({ title, items }: { title: string; items: string[] })}
	<div class="space-y-4">
		<div>
			<h3 class="text-xs font-semibold tracking-widest text-foreground/50 uppercase">{title}</h3>
		</div>
		<ul class="space-y-3">
			{#each items as item}
				<li
					class="group block cursor-pointer text-sm text-foreground transition-colors hover:text-secondary"
				>
					<div>
						{item}
					</div>
				</li>
			{/each}
		</ul>
	</div>
{/snippet}

{#snippet ShopContent()}
	<div class="grid grid-cols-3 gap-8">
		{@render ListColumn({
			title: 'Featured',
			items: ['New Arrivals', 'Best Sellers', 'Trending Now']
		})}
		{@render ListColumn({ title: 'Collections', items: ['Eco-friendly', 'Handmade', 'Vintage'] })}
		{@render ListColumn({ title: 'Deals', items: ['Active discounts', 'Bundle deals'] })}
	</div>
{/snippet}

{#snippet CategoriesContent()}
	<div class="grid grid-cols-3 gap-8">
		{@render ListColumn({
			title: 'Home & Living',
			items: ['Furniture & decor', 'Textiles', 'Kitchen', 'Bathroom']
		})}
		{@render ListColumn({
			title: 'Tech & Gadgets',
			items: ['Phones', 'Laptops', 'Cameras', 'Tech Accessories']
		})}
		{@render ListColumn({
			title: 'Personal care',
			items: ['Skincare', 'Perfumes', 'Shampoos & conditioners', 'Fragrances']
		})}
		{@render ListColumn({ title: 'Fashion', items: ['Clothes', 'Shoes', 'Jewelry'] })}
		{@render ListColumn({
			title: 'Sports',
			items: ['Fitness', 'Outdoor', 'Team Sports', 'Water Sports']
		})}
	</div>
{/snippet}

{#snippet ActionCard(items: { title: string; desc: string; icon: any }[])}
	<div class="grid grid-cols-2 gap-x-8 gap-y-4">
		{#each items as item}
			{@const Icon = item.icon}
			<a
				href="#"
				class="group flex items-start gap-4 rounded-xl p-3 transition-colors hover:bg-secondary-tonal/50"
			>
				<div
					class="flex size-10 items-center justify-center text-secondary transition-colors group-hover:text-secondary"
				>
					<Icon class="size-5" />
				</div>
				<div class="space-y-1">
					<p
						class="text-sm leading-none font-medium text-foreground transition-colors group-hover:text-secondary"
					>
						{item.title}
					</p>
					<p class="text-sm text-foreground/50 group-hover:text-foreground">{item.desc}</p>
				</div>
			</a>
		{/each}
	</div>
{/snippet}

{#snippet OrdersContent()}
	{@render ActionCard([
		{
			title: 'Track orders',
			desc: 'Get real-time updates on your packages',
			icon: Package
		},
		{
			title: 'Order history',
			desc: 'View and manage your past purchases',
			icon: Receipt
		},
		{
			title: 'Returns & Exchanges',
			desc: 'Hassle-free returns within 30 days',
			icon: Exchange
		},
		{
			title: 'My wishlist',
			desc: 'Items you have saved for later',
			icon: Heart
		}
	])}
{/snippet}

{#snippet AccountContent()}
	{@render ActionCard([
		{
			title: 'Profile Info',
			desc: 'Manage your personal details',
			icon: User
		},
		{
			title: 'Security',
			desc: 'Passwords and authentication',
			icon: ShieldLock
		},
		{
			title: 'Payment Methods',
			desc: 'Cards and billing addresses',
			icon: CreditCard
		},
		{
			title: 'Notifications',
			desc: 'Manage your email and SMS alerts',
			icon: BellRinging
		}
	])}
{/snippet}

<div class="flex items-center justify-center text-sm">
	{#each [{ label: 'Shop', render: ShopContent, content: 'And discover the full marketplace.' }, { label: 'Categories', href: '/categories', render: CategoriesContent, content: 'Browse an extensive range of products.' }, { label: 'Orders', render: OrdersContent, content: 'Track your shopping journey and manage your purchases.' }, { label: 'Account', render: AccountContent, content: 'Personalize your experience and your security.' }, { label: 'Support', href: '/support', content: 'Personalize your experience and manage your security settings.' }] as link}
		<Button
			variant="ghost"
			color={'secondary'}
			href={link.href ?? '#'}
			class="font-normal text-primary hover:text-secondary"
			onmouseenter={() => onHover(link)}
		>
			{link.label}
		</Button>
	{/each}
</div>
