// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import type { UserProfile } from '$lib/api/types';

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			is_authenticated: boolean;
			password_expired: boolean;
			user: UserProfile | null;
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
