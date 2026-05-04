import { apiFetch } from '$lib/api/client';
import type { EmbeddedUser, SignupResponse } from '$lib/api/types';
import type { RequestEvent } from '@sveltejs/kit';
import { forwardCookies } from '../cookies';

/**
 * Standard Signup Result.
 */
export interface SignupResult {
	success: boolean;
	status_code: number;
	user?: EmbeddedUser;
	error?: string;
	fieldErrors?: Record<string, string>;
}

/**
 * Creates a new account and manually forwards JWT cookies from Django to the Browser.
 */
export const signup = async (
	full_name: string,
	email: string,
	password: string,
	customFetch: typeof fetch,
	event: RequestEvent
): Promise<SignupResult> => {
	const res = await apiFetch<SignupResponse>(
		'/users/management/',
		{
			method: 'POST',
			body: JSON.stringify({ full_name, email, password })
		},
		customFetch
	);

	// --- COOKIE FORWARDING LOGIC ---
	if (res.ok && res.headers) {
		forwardCookies(res.headers, event);
	}

	if (!res.ok) {
		const { error, status } = res;

		if (Object.keys(error.errors).length > 0) {
			return {
				success: false,
				status_code: status,
				fieldErrors: {
					email: error.errors.email?.[0] || '',
					full_name: error.errors.full_name?.[0] || '',
					password: error.errors.password?.[0] || ''
				}
			};
		}

		return {
			success: false,
			status_code: status,
			error: error.detail || 'Registration failed.'
		};
	}

	return {
		success: true,
		status_code: res.status,
		user: res.data.user
	};
};
