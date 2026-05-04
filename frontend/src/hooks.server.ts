import { refreshToken, getUserProfile } from '$lib/server/auth/session';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	let access_token = event.cookies.get('access_token');
	const refresh_token = event.cookies.get('refresh_token');
	const access_token_expires = event.cookies.get('access_token_expires');

	// DEBUG: log every incoming request and its cookies
	console.log(`\n[hook] ${event.request.method} ${event.url.pathname}`);
	console.log(`[hook] access_token present: ${!!access_token}`);
	console.log(`[hook] refresh_token present: ${!!refresh_token}`);
	console.log(`[hook] access_token_expires: ${access_token_expires}`);

	const now = Math.floor(Date.now() / 1000);
	const is_expired = access_token_expires ? parseInt(access_token_expires) <= now : false;
	console.log(`[hook] is_expired: ${is_expired}`);

	// ─── 1. AUTO-REFRESH LOGIC (Section 7) ────────────────────────────────────
	if (refresh_token && (!access_token || is_expired)) {
		console.log('[hook] Attempting token refresh...');
		const refreshed = await refreshToken(event);

		if (refreshed) {
			access_token = event.cookies.get('access_token');
			console.log('[hook] Token refresh SUCCESS. New access_token present:', !!access_token);
		} else {
			console.log('[hook] Token refresh FAILED. Clearing cookies.');
			event.cookies.delete('access_token', { path: '/' });
			event.cookies.delete('refresh_token', { path: '/' });
			event.cookies.delete('access_token_expires', { path: '/' });
			event.locals.is_authenticated = false;
			event.locals.user = null;
			return resolve(event);
		}
	}

	if (!access_token) {
		console.log('[hook] No access_token — unauthenticated.');
		event.locals.is_authenticated = false;
		event.locals.password_expired = false;
		event.locals.user = null;
		return resolve(event);
	}

	// ─── 2. SESSION VALIDATION & IDENTITY ───────────────────────────────────
	console.log('[hook] Fetching user profile to validate session...');
	const user = await getUserProfile(event.fetch, access_token);

	if (!user) {
		console.log('[hook] getUserProfile returned null — clearing cookies.');
		event.cookies.delete('access_token', { path: '/' });
		event.cookies.delete('refresh_token', { path: '/' });
		event.cookies.delete('access_token_expires', { path: '/' });
		event.locals.is_authenticated = false;
		event.locals.password_expired = false;
		event.locals.user = null;
		return resolve(event);
	}

	console.log('[hook] Session valid. User:', user.email);

	// Populate locals with full profile
	event.locals.is_authenticated = true;
	event.locals.password_expired = user.password_expired;
	event.locals.user = user;

	return resolve(event);
};
