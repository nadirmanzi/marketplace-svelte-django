
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```sh
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const SHELL: string;
	export const SESSION_MANAGER: string;
	export const XDG_CONFIG_DIRS: string;
	export const XDG_SESSION_PATH: string;
	export const XDG_MENU_PREFIX: string;
	export const ICEAUTHORITY: string;
	export const MEMORY_PRESSURE_WRITE: string;
	export const DESKTOP_SESSION: string;
	export const GTK_RC_FILES: string;
	export const XDG_SEAT: string;
	export const PWD: string;
	export const LOGNAME: string;
	export const XDG_SESSION_DESKTOP: string;
	export const XDG_SESSION_TYPE: string;
	export const SYSTEMD_EXEC_PID: string;
	export const XAUTHORITY: string;
	export const MOTD_SHOWN: string;
	export const XKB_DEFAULT_MODEL: string;
	export const GTK2_RC_FILES: string;
	export const HOME: string;
	export const LANG: string;
	export const _JAVA_AWT_WM_NONREPARENTING: string;
	export const XDG_CURRENT_DESKTOP: string;
	export const MEMORY_PRESSURE_WATCH: string;
	export const WAYLAND_DISPLAY: string;
	export const XDG_SEAT_PATH: string;
	export const INVOCATION_ID: string;
	export const MANAGERPID: string;
	export const KDE_SESSION_UID: string;
	export const XKB_DEFAULT_LAYOUT: string;
	export const XDG_SESSION_CLASS: string;
	export const USER: string;
	export const QT_WAYLAND_RECONNECT: string;
	export const KDE_SESSION_VERSION: string;
	export const DISPLAY: string;
	export const SHLVL: string;
	export const XDG_VTNR: string;
	export const XDG_SESSION_ID: string;
	export const MANAGERPIDFDID: string;
	export const XDG_RUNTIME_DIR: string;
	export const DEBUGINFOD_URLS: string;
	export const JOURNAL_STREAM: string;
	export const XDG_DATA_DIRS: string;
	export const KDE_FULL_SESSION: string;
	export const PATH: string;
	export const DBUS_SESSION_BUS_ADDRESS: string;
	export const KDE_APPLICATIONS_AS_SCOPE: string;
	export const MAIL: string;
	export const XKB_DEFAULT_OPTIONS: string;
	export const OLDPWD: string;
	export const _: string;
	export const CHROME_DESKTOP: string;
	export const FC_FONTATIONS: string;
	export const GDK_BACKEND: string;
	export const NO_AT_BRIDGE: string;
	export const TERM_PROGRAM: string;
	export const TERM_PROGRAM_VERSION: string;
	export const COLORTERM: string;
	export const GIT_ASKPASS: string;
	export const VSCODE_GIT_ASKPASS_NODE: string;
	export const VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
	export const VSCODE_GIT_ASKPASS_MAIN: string;
	export const VSCODE_GIT_IPC_HANDLE: string;
	export const PYDEVD_DISABLE_FILE_VALIDATION: string;
	export const VSCODE_DEBUGPY_ADAPTER_ENDPOINTS: string;
	export const BUNDLED_DEBUGPY_PATH: string;
	export const GK_GL_ADDR: string;
	export const GK_GL_PATH: string;
	export const PYTHONSTARTUP: string;
	export const PYTHON_BASIC_REPL: string;
	export const VSCODE_INJECTION: string;
	export const ZDOTDIR: string;
	export const USER_ZDOTDIR: string;
	export const TERM: string;
	export const ZSH: string;
	export const PAGER: string;
	export const LESS: string;
	export const LSCOLORS: string;
	export const LS_COLORS: string;
	export const FNM_MULTISHELL_PATH: string;
	export const FNM_VERSION_FILE_STRATEGY: string;
	export const FNM_DIR: string;
	export const FNM_LOGLEVEL: string;
	export const FNM_NODE_DIST_MIRROR: string;
	export const FNM_COREPACK_ENABLED: string;
	export const FNM_RESOLVE_ENGINES: string;
	export const FNM_ARCH: string;
	export const VSCODE_PYTHON_AUTOACTIVATE_GUARD: string;
	export const PS1: string;
	export const npm_config_local_prefix: string;
	export const npm_config_user_agent: string;
	export const npm_execpath: string;
	export const npm_package_name: string;
	export const npm_package_json: string;
	export const npm_package_version: string;
	export const NODE: string;
	export const npm_node_execpath: string;
	export const npm_command: string;
	export const npm_lifecycle_event: string;
	export const npm_lifecycle_script: string;
	export const NODE_ENV: string;
}

/**
 * Similar to [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > [!NOTE] In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		SHELL: string;
		SESSION_MANAGER: string;
		XDG_CONFIG_DIRS: string;
		XDG_SESSION_PATH: string;
		XDG_MENU_PREFIX: string;
		ICEAUTHORITY: string;
		MEMORY_PRESSURE_WRITE: string;
		DESKTOP_SESSION: string;
		GTK_RC_FILES: string;
		XDG_SEAT: string;
		PWD: string;
		LOGNAME: string;
		XDG_SESSION_DESKTOP: string;
		XDG_SESSION_TYPE: string;
		SYSTEMD_EXEC_PID: string;
		XAUTHORITY: string;
		MOTD_SHOWN: string;
		XKB_DEFAULT_MODEL: string;
		GTK2_RC_FILES: string;
		HOME: string;
		LANG: string;
		_JAVA_AWT_WM_NONREPARENTING: string;
		XDG_CURRENT_DESKTOP: string;
		MEMORY_PRESSURE_WATCH: string;
		WAYLAND_DISPLAY: string;
		XDG_SEAT_PATH: string;
		INVOCATION_ID: string;
		MANAGERPID: string;
		KDE_SESSION_UID: string;
		XKB_DEFAULT_LAYOUT: string;
		XDG_SESSION_CLASS: string;
		USER: string;
		QT_WAYLAND_RECONNECT: string;
		KDE_SESSION_VERSION: string;
		DISPLAY: string;
		SHLVL: string;
		XDG_VTNR: string;
		XDG_SESSION_ID: string;
		MANAGERPIDFDID: string;
		XDG_RUNTIME_DIR: string;
		DEBUGINFOD_URLS: string;
		JOURNAL_STREAM: string;
		XDG_DATA_DIRS: string;
		KDE_FULL_SESSION: string;
		PATH: string;
		DBUS_SESSION_BUS_ADDRESS: string;
		KDE_APPLICATIONS_AS_SCOPE: string;
		MAIL: string;
		XKB_DEFAULT_OPTIONS: string;
		OLDPWD: string;
		_: string;
		CHROME_DESKTOP: string;
		FC_FONTATIONS: string;
		GDK_BACKEND: string;
		NO_AT_BRIDGE: string;
		TERM_PROGRAM: string;
		TERM_PROGRAM_VERSION: string;
		COLORTERM: string;
		GIT_ASKPASS: string;
		VSCODE_GIT_ASKPASS_NODE: string;
		VSCODE_GIT_ASKPASS_EXTRA_ARGS: string;
		VSCODE_GIT_ASKPASS_MAIN: string;
		VSCODE_GIT_IPC_HANDLE: string;
		PYDEVD_DISABLE_FILE_VALIDATION: string;
		VSCODE_DEBUGPY_ADAPTER_ENDPOINTS: string;
		BUNDLED_DEBUGPY_PATH: string;
		GK_GL_ADDR: string;
		GK_GL_PATH: string;
		PYTHONSTARTUP: string;
		PYTHON_BASIC_REPL: string;
		VSCODE_INJECTION: string;
		ZDOTDIR: string;
		USER_ZDOTDIR: string;
		TERM: string;
		ZSH: string;
		PAGER: string;
		LESS: string;
		LSCOLORS: string;
		LS_COLORS: string;
		FNM_MULTISHELL_PATH: string;
		FNM_VERSION_FILE_STRATEGY: string;
		FNM_DIR: string;
		FNM_LOGLEVEL: string;
		FNM_NODE_DIST_MIRROR: string;
		FNM_COREPACK_ENABLED: string;
		FNM_RESOLVE_ENGINES: string;
		FNM_ARCH: string;
		VSCODE_PYTHON_AUTOACTIVATE_GUARD: string;
		PS1: string;
		npm_config_local_prefix: string;
		npm_config_user_agent: string;
		npm_execpath: string;
		npm_package_name: string;
		npm_package_json: string;
		npm_package_version: string;
		NODE: string;
		npm_node_execpath: string;
		npm_command: string;
		npm_lifecycle_event: string;
		npm_lifecycle_script: string;
		NODE_ENV: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
