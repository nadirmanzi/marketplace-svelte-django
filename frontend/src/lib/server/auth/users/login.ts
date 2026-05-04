import { apiFetch } from '$lib/api/client';
import type { LoginResponse } from '$lib/api/types';
import type { RequestEvent } from '@sveltejs/kit';
import { forwardCookies } from '../cookies';

/**
 * Standard Login Result.
 */
export interface LoginResult {
	success: boolean;
	user?: LoginResponse['user'];
	error?: string;
	code?: string;
	fieldErrors?: Record<string, string>;
}

/**
 * Authenticates user and manually forwards JWT cookies from Django to the Browser.
 */
export const login = async (
	email: string,
	password: string,
	customFetch: typeof fetch,
	event: RequestEvent
): Promise<LoginResult> => {
	console.log('[login] Calling apiFetch for login...');

	const res = await apiFetch<LoginResponse>(
		'/users/auth/login/',
		{
			method: 'POST',
			body: JSON.stringify({ email, password })
		},
		customFetch
	);

	console.log('[login] apiFetch result: ok=', res.ok, 'status=', res.status);
	console.log('[login] Response headers present:', !!res.headers);

	if (res.headers) {
		// Log raw set-cookie header presence
		const setCookieRaw = res.headers.get('set-cookie');
		console.log('[login] set-cookie header (raw):', setCookieRaw ? setCookieRaw.substring(0, 200) : 'null');
		const hasGetSetCookie = typeof (res.headers as any).getSetCookie === 'function';
		console.log('[login] headers.getSetCookie is function:', hasGetSetCookie);
		if (hasGetSetCookie) {
			const cookies = (res.headers as any).getSetCookie();
			console.log('[login] getSetCookie() array length:', cookies.length);
		}
	}

	// --- COOKIE FORWARDING LOGIC ---
	if (res.ok && res.headers) {
		console.log('[login] Calling forwardCookies...');
		forwardCookies(res.headers, event);
		console.log('[login] forwardCookies returned.');
	} else if (!res.ok) {
		console.log('[login] Login failed — not forwarding cookies.');
		// Also forward cookies on error in case of password_expired scenario
		if (res.headers) {
			forwardCookies(res.headers, event);
		}
	}

	if (!res.ok) {
		const { error } = res;

		// Handle Field Validation
		if (Object.keys(error.errors).length > 0) {
			return {
				success: false,
				fieldErrors: {
					email: error.errors.email?.[0] || '',
					password: error.errors.password?.[0] || ''
				}
			};
		}

		// Handle Specialized Error Codes
		if (error.code === 'password_expired') {
			return {
				success: true, // We treat this as a "partial success" redirecting to password change
				user: (error as any).user,
				code: 'password_expired',
				error: error.detail
			};
		}

		return {
			success: false,
			code: error.code,
			error: error.detail || 'Authentication failed.'
		};
	}

	return {
		success: true,
		user: res.data.user
	};
};
