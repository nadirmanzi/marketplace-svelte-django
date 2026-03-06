
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
		RouteId(): "/(main)" | "/" | "/auth" | "/auth/login" | "/(main)/browse" | "/(main)/categories";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/(main)": Record<string, never>;
			"/": Record<string, never>;
			"/auth": Record<string, never>;
			"/auth/login": Record<string, never>;
			"/(main)/browse": Record<string, never>;
			"/(main)/categories": Record<string, never>
		};
		Pathname(): "/" | "/auth/login" | "/browse" | "/categories";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/banner.webp" | string & {};
	}
}