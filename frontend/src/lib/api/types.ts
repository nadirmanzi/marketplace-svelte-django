/**
 * Standard API error structure.
 */
export interface ApiError {
    success: false;
    code: string;
    detail: string;
    errors: Record<string, string[]>; // Field-based validation errors
}

/**
 * Standard API success structure (optional wrapper, some endpoints return data directly).
 */
export interface ApiSuccess<T> {
    success: true;
    data: T;
}

/**
 * Discriminated union for API return results.
 */
export type ApiResult<T> = 
    | { ok: true; status: number; data: T; error: null; headers: Headers }
    | { ok: false; status: number; error: ApiError; data: null; headers: Headers | null };

/**
 * Standard User Profile as per Section 6 of the API Guide.
 */
export interface UserProfile {
    user_id: string; // UUID
    email: string;
    full_name: string;
    telephone_number: string | null;
    password_changed_at: string; // ISO DateTime
    password_expired: boolean;
    created_at: string; // ISO DateTime
    updated_at: string; // ISO DateTime
}

/**
 * Response for POST /users/auth/login/
 */
export interface LoginResponse {
    user: {
        user_id: string;
        email: string;
        full_name: string;
    };
}

/**
 * Response for POST /users/management/ (Signup)
 */
export type SignupResponse = UserProfile;

/**
 * Response for GET /users/management/me/
 */
export type MeResponse = UserProfile;
