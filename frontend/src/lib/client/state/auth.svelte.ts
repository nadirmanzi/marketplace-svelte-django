import type { UserProfile } from "$lib/api/types";

interface AuthState {
    is_authenticated: boolean;
    password_expired: boolean;
    user: UserProfile | null;
}

export const auth_state: AuthState = $state({
    is_authenticated: false,
    password_expired: false,
    user: null,
})

export const setAuth = (user: UserProfile) => {
    auth_state.is_authenticated = true
    auth_state.password_expired = user.password_expired
    auth_state.user = user
}

export const setPasswordExpired = (is_expired: boolean) => {
    auth_state.password_expired = is_expired
}

export const revokeAuth = () => {
    auth_state.is_authenticated = false
    auth_state.password_expired = false
    auth_state.user = null
}