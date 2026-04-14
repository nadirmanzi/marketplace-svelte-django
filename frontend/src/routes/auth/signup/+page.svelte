<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Mail from '@tabler/icons-svelte-runes/icons/mail';
	import Key from '@tabler/icons-svelte-runes/icons/key';
	import Signup from '$lib/assets/signup.jpg';
	import Eye from '@tabler/icons-svelte-runes/icons/eye';
	import EyeOff from '@tabler/icons-svelte-runes/icons/eye-off';
	import X from '@tabler/icons-svelte-runes/icons/x';
	import { superForm } from 'sveltekit-superforms';
	import { zod4Client } from 'sveltekit-superforms/adapters';
	import { signup_schema } from '$lib/schemas/auth';
	import User from '@tabler/icons-svelte-runes/icons/user';
	import { fly, slide } from 'svelte/transition';

	let { data } = $props();

	const {
		form: validated_form,
		errors,
		message,
		enhance,
		delayed
	} = superForm(data.form, {
		validators: zod4Client(signup_schema),
		validationMethod: 'oninput'
	});

	let password_type = $state<'password' | 'text'>('password');
	let confirm_password_type = $state<'password' | 'text'>('password');

	function toggle_password_type() {
		password_type = password_type === 'password' ? 'text' : 'password';
	}

	function toggle_confirm_password_type() {
		confirm_password_type = confirm_password_type === 'password' ? 'text' : 'password';
	}
</script>

<main class="grid h-full grid-cols-2">
	<section class="relative">
		<img src={Signup} alt="" class="h-full w-full object-cover" />
		<div
			class="absolute inset-0 top-0 flex h-20 w-full items-center justify-end bg-linear-to-b from-black/80 via-black/60 to-transparent px-10"
		>
			{#if $message?.type === 'error'}
				<div in:fly={{ x: 100, duration: 200 }} class="rounded-lg bg-destructive-tonal px-6 py-4">
					<p class="text-center text-sm text-on-destructive-tonal">
						{$message.text}
					</p>
				</div>
			{/if}
		</div>
	</section>

	<section class="relative overflow-hidden bg-surface">
		<div class="absolute top-20 left-1/2 w-3/5 -translate-x-1/2 space-y-16 p-1">
			<!-- HEADER -->
			<div class="space-y-4">
				<div class="flex items-center space-x-4 font-display text-2xl font-bold">
					<p>Welcome to</p>
					<p
						class="inline-flex items-center justify-center rounded-full bg-secondary px-3 py-1 text-base text-on-secondary"
					>
						Amazon V2
					</p>
				</div>
				<p class="text-surface-foreground-muted">Create your account and shop effortlessly</p>
			</div>

			<!-- FORM -->
			<form method="POST" use:enhance class="space-y-12">
				<div class="space-y-6">
					<!-- Full Name -->
					<Input
						context="surface"
						name="full_name"
						label="Full name"
						type="text"
						placeholder="John Doe"
						error={$errors?.full_name?.[0]}
						bind:value={$validated_form.full_name}
					>
						{#snippet leading()}
							<User class="size-5" stroke-width={1.5} />
						{/snippet}
						{#snippet trailing()}
							{#if $validated_form.full_name}
								<button type="button" onclick={() => ($validated_form.full_name = '')}>
									<X class="size-5" stroke-width={1.5} />
								</button>
							{/if}
						{/snippet}
					</Input>

					<!-- Email -->
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

					<!-- Password -->
					<Input
						context="surface"
						name="password"
						label="Password"
						type={password_type}
						placeholder="***********"
						error={$errors?.password?.[0]}
						bind:value={$validated_form.password}
					>
						{#snippet leading()}
							<Key />
						{/snippet}
						{#snippet trailing()}
							{#if $validated_form.password}
								<button type="button" onclick={toggle_password_type}>
									{#if password_type === 'password'}
										<Eye class="size-5" stroke-width={1.5} />
									{:else}
										<EyeOff class="size-5" stroke-width={1.5} />
									{/if}
								</button>
							{/if}
						{/snippet}
					</Input>

					<!-- Confirm Password -->
					<Input
						context="surface"
						name="confirm_password"
						label="Confirm password"
						type={confirm_password_type}
						placeholder="***********"
						error={$errors?.confirm_password?.[0]}
						bind:value={$validated_form.confirm_password}
					>
						{#snippet leading()}
							<Key />
						{/snippet}
						{#snippet trailing()}
							{#if $validated_form.confirm_password}
								<button type="button" onclick={toggle_confirm_password_type}>
									{#if confirm_password_type === 'password'}
										<Eye class="size-5" stroke-width={1.5} />
									{:else}
										<EyeOff class="size-5" stroke-width={1.5} />
									{/if}
								</button>
							{/if}
						{/snippet}
					</Input>
				</div>

				<Button
					type="submit"
					class="w-full text-base"
					variant="filled"
					disabled={!$validated_form.full_name ||
						!$validated_form.email ||
						!$validated_form.password ||
						!$validated_form.confirm_password ||
						$errors.full_name ||
						$errors.email ||
						$errors.password ||
						$errors.confirm_password ||
						$delayed}
					color="primary"
				>
					{$delayed ? 'Signing up...' : 'Sign up'}
				</Button>
			</form>

			<!-- LOGIN -->
			<p class="">
				Already have an account? <a href="/auth/login" class=" text-secondary">Login</a>
			</p>
		</div>
	</section>
</main>
