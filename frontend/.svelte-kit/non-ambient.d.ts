
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/(main)" | "/" | "/auth" | "/auth/login" | "/auth/logout" | "/auth/signup" | "/(main)/categories" | "/(main)/orders" | "/ui" | "/ui/button" | "/ui/input" | "/ui/sheet";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/(main)": Record<string, never>;
			"/": Record<string, never>;
			"/auth": Record<string, never>;
			"/auth/login": Record<string, never>;
			"/auth/logout": Record<string, never>;
			"/auth/signup": Record<string, never>;
			"/(main)/categories": Record<string, never>;
			"/(main)/orders": Record<string, never>;
			"/ui": Record<string, never>;
			"/ui/button": Record<string, never>;
			"/ui/input": Record<string, never>;
			"/ui/sheet": Record<string, never>
		};
		Pathname(): "/" | "/auth/login" | "/auth/logout" | "/auth/signup" | "/categories" | "/orders" | "/ui" | "/ui/button" | "/ui/input" | "/ui/sheet";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/robots.txt" | string & {};
	}
}