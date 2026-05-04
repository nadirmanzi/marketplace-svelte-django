import type { RequestEvent } from '@sveltejs/kit';

/**
 * Standardizes cookie relay from Django (Backend) to Browser via SvelteKit.
 *
 * This utility handles:
 * 1. Robust parsing of Set-Cookie headers (case-insensitive, regex-based).
 * 2. Cross-environment security (forces secure: false on localhost to prevent browser rejection).
 * 3. CORS credentials bridging (adds Access-Control-Allow-Credentials: true).
 */
export function forwardCookies(headers: Headers, event: RequestEvent): void {
	console.log('[forwardCookies] Called. Event URL hostname:', event.url.hostname);

	// 1. Extract raw cookies from backend response
	let backendCookies: string[] = [];
	if (typeof headers.getSetCookie === 'function') {
		backendCookies = headers.getSetCookie();
		console.log('[forwardCookies] getSetCookie() count:', backendCookies.length);
		console.log('[forwardCookies] getSetCookie() raw:', JSON.stringify(backendCookies));
	} else {
		console.log('[forwardCookies] headers.getSetCookie is NOT a function');
	}

	// Fallback if getSetCookie doesn't exist or returns a single merged string
	if (
		!backendCookies ||
		backendCookies.length === 0 ||
		(backendCookies.length === 1 && backendCookies[0].includes(', '))
	) {
		const raw = headers.get('set-cookie') || (backendCookies.length === 1 ? backendCookies[0] : null);
		console.log('[forwardCookies] Fallback raw set-cookie header:', raw ? raw.substring(0, 200) : 'null');
		if (raw) {
			// Split by comma only if followed by a cookie name and equals sign
			// This prevents splitting the comma inside 'Expires=Mon, 01 Jan...'
			backendCookies = raw.split(/,(?=\s*[a-zA-Z0-9_-]+\s*=)/).map((s) => s.trim());
			console.log('[forwardCookies] After regex split, cookie count:', backendCookies.length);
		}
	}

	console.log('[forwardCookies] Final cookie count to process:', backendCookies.length);

	if (backendCookies.length === 0) {
		console.log('[forwardCookies] No cookies found — returning early.');
		return;
	}

	// 2. Explicitly allow credentials for fetch-based form submissions (use:enhance)
	event.setHeaders({
		'Access-Control-Allow-Credentials': 'true'
	});

	backendCookies.forEach((cookieString, i) => {
		console.log(`[forwardCookies] Cookie[${i}] raw string:`, cookieString.substring(0, 120));

		// 3. Robust attribute extraction
		const parts = cookieString.split(/;\s*/);
		const nameValue = parts[0];
		if (!nameValue) {
			console.log(`[forwardCookies] Cookie[${i}] skipped: empty nameValue`);
			return;
		}

		const firstEq = nameValue.indexOf('=');
		if (firstEq === -1) {
			console.log(`[forwardCookies] Cookie[${i}] skipped: no '=' in nameValue`);
			return;
		}

		const name = nameValue.slice(0, firstEq);
		const value = nameValue.slice(firstEq + 1);

		const attributes = parts.slice(1).reduce(
			(acc, part) => {
				const [k, ...vParts] = part.split('=');
				acc[k.toLowerCase().trim()] = vParts.join('=') || true;
				return acc;
			},
			{} as Record<string, string | boolean>
		);

		console.log(`[forwardCookies] Cookie[${i}] name="${name}", attributes:`, JSON.stringify(attributes));

		const maxAge =
			typeof attributes['max-age'] === 'string' ? parseInt(attributes['max-age']) : undefined;

		// 4. Localhost Security Override
		const isLocalhost = event.url.hostname === 'localhost' || event.url.hostname === '127.0.0.1';
		const secure = isLocalhost ? false : !!attributes['secure'];

		try {
			event.cookies.set(name, value, {
				path: (attributes['path'] as string) || '/',
				httpOnly: !!attributes['httponly'],
				secure: secure,
				sameSite: 'lax',
				maxAge: maxAge
			});
			console.log(`[forwardCookies] ✓ Set cookie: ${name}`);
		} catch (err) {
			console.error(`[forwardCookies] ✗ FAILED to set cookie: ${name}`, err);
		}
	});
}
