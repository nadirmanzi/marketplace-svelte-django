import type { RequestEvent } from "@sveltejs/kit";

/**
 * Standardizes cookie relay from Django (Backend) to Browser via SvelteKit.
 * 
 * This utility handles:
 * 1. Robust parsing of Set-Cookie headers (case-insensitive, regex-based).
 * 2. Cross-environment security (forces secure: false on localhost to prevent browser rejection).
 * 3. CORS credentials bridging (adds Access-Control-Allow-Credentials: true).
 */
export function forwardCookies(headers: Headers, event: RequestEvent): void {
    // 1. Extract raw cookies from backend response
    let backendCookies: string[] = [];
    if (headers.getSetCookie) {
        backendCookies = headers.getSetCookie();
    } else {
        const raw = headers.get('set-cookie');
        if (raw) {
            backendCookies = [raw]; 
        }
    }

    if (backendCookies.length === 0) return;

    // 2. Explicitly allow credentials for fetch-based form submissions (use:enhance)
    event.setHeaders({
        'Access-Control-Allow-Credentials': 'true'
    });
    
    backendCookies.forEach(cookieString => {
        // 3. Robust attribute extraction
        const parts = cookieString.split(/;\s*/);
        const nameValue = parts[0];
        if (!nameValue) return;

        const firstEq = nameValue.indexOf('=');
        if (firstEq === -1) return;

        const name = nameValue.slice(0, firstEq);
        const value = nameValue.slice(firstEq + 1);

        const attributes = parts.slice(1).reduce((acc, part) => {
            const [k, ...vParts] = part.split('=');
            acc[k.toLowerCase()] = vParts.join('=') || true;
            return acc;
        }, {} as Record<string, string | boolean>);

        const maxAge = typeof attributes['max-age'] === 'string' ? parseInt(attributes['max-age']) : undefined;
        
        // 4. Localhost Security Override
        const isLocalhost = event.url.hostname === 'localhost' || event.url.hostname === '127.0.0.1';
        const secure = isLocalhost ? false : !!attributes['secure'];

        event.cookies.set(name, value, {
            path: (attributes['path'] as string) || '/',
            httpOnly: !!attributes['httponly'],
            secure: secure,
            // Omit explicit SameSite to let browser use safe defaults on insecure localhost
            sameSite: undefined, 
            maxAge: maxAge
        });
    });
}
