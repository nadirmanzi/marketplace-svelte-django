<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Mail from '@tabler/icons-svelte-runes/icons/mail';
	import Key from '@tabler/icons-svelte-runes/icons/key';
	import LoginShopping from '$lib/assets/login-shopping.jpg';
	import Eye from '@tabler/icons-svelte-runes/icons/eye';
	import EyeOff from '@tabler/icons-svelte-runes/icons/eye-off';
	import X from '@tabler/icons-svelte-runes/icons/x';
	import { superForm } from 'sveltekit-superforms';
	import { zod4Client } from 'sveltekit-superforms/adapters';
	import { login_schema } from '$lib/schemas/auth.js';
	import { fly, slide } from 'svelte/transition';
	import Logo from '$lib/components/logo.svelte';

	let { data } = $props();
	const {
		form: validated_form,
		errors,
		message,
		enhance,
		delayed
	} = superForm(data.form, {
		validators: zod4Client(login_schema),
		validationMethod: 'oninput'
	});

	let password_type = $state<'password' | 'text'>('password');

	function toggle_password_type() {
		password_type = password_type === 'password' ? 'text' : 'password';
	}
</script>

<main class="grid h-full grid-cols-5">
	<section class="relative col-span-2 overflow-hidden bg-surface">
		<div class="absolute top-40 left-1/2 w-2/3 -translate-x-1/2 space-y-16 p-1">
			<!-- HEADER -->
			<div class="space-y-4">
				<div class="flex items-center space-x-4 font-display text-2xl font-extrabold">
					<p>Login to</p>
					<p
						class="inline-flex items-center justify-center rounded-full bg-secondary px-3 py-1 text-base text-on-secondary"
					>
						Amazon V2
					</p>
				</div>
				<p class="text-surface-foreground-muted">Enter your credentials to access your account</p>
			</div>

			<!-- FORM -->
			<form method="POST" use:enhance class="space-y-12">
				<div class="space-y-6">
					<Input
						context="surface"
						name="email"
						label="Email address"
						type="email"
						placeholder="example@email.com"
						error={$errors?.email?.[0]}
						bind:value={$validated_form.email}
					>
						{#snippet leading()}
							<Mail />
						{/snippet}

						{#snippet trailing()}
							{#if $validated_form.email}
								<button type="button" onclick={() => ($validated_form.email = '')}>
									<X class="size-5" stroke-width={1.5} />
								</button>
							{/if}
						{/snippet}
					</Input>

					<div class="space-y-2">
						<Input
							context="surface"
							name="password"
							label="Password"
							type={password_type}
							placeholder="***********"
							bind:value={$validated_form.password}
							error={$errors?.password?.[0]}
						>
							{#snippet leading()}
								<Key />
							{/snippet}

							{#snippet trailing()}
								{#if $validated_form.password}
									{#if password_type === 'password'}
										<button type="button" onclick={toggle_password_type}>
											<Eye class="size-5" stroke-width={1.5} />
										</button>
									{:else}
										<button type="button" onclick={toggle_password_type}>
											<EyeOff class="size-5" stroke-width={1.5} />
										</button>
									{/if}
								{/if}
							{/snippet}
						</Input>
						<a href="#" class="block w-full text-end text-sm font-medium text-secondary"
							>Forgot password?</a
						>
					</div>
				</div>

				<Button
					type="submit"
					class="w-full text-base"
					variant="filled"
					disabled={!$validated_form.email ||
						!$validated_form.password ||
						$errors.email ||
						$errors.password ||
						$delayed}
					color="primary">{$delayed ? 'Logging in...' : 'Login'}</Button
				>
			</form>

			<!-- SIGN UP -->
			<p class="">
				Don't have an account? <a href="/auth/signup" class=" text-secondary">Sign up</a>
			</p>
		</div>
	</section>

	<section class="relative col-span-3">
		<img src={LoginShopping} alt="" class="h-full w-full object-cover" />
		<div
			class="absolute inset-0 top-0 flex h-20 w-full items-center justify-start bg-linear-to-b from-black/80 via-black/60 to-transparent px-10"
		>
			{#if $message?.type === 'error'}
				<div
					in:fly={{ x: '-100', duration: 200 }}
					class="rounded-lg bg-destructive-tonal px-6 py-4"
				>
					<p
						class="rounded-full bg-destructive-tonal text-center text-sm text-on-destructive-tonal"
					>
						{$message.text}
					</p>
				</div>
			{/if}
		</div>
	</section>
</main>

<style>
</style>
