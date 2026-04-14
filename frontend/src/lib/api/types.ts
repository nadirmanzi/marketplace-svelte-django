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
 * Standard API error structure.
 */
export interface ApiError {
    detail?: string;
    code?: string;
    user?: TruncatedUser;
    errors?: Record<string, string[]>; // Field-based validation errors
    non_field_errors?: string[];
    messages?: Array<{
        token_class: string;
        token_type: string;
        message: string;
    }>;
}

/**
 * Truncated user info returned by standard login.
 */
export interface TruncatedUser {
    user_id: string;
    email: string;
}

/**
 * Response for POST /users/auth/login/
 */
export interface LoginResponse {
    user?: TruncatedUser;
    error?: 'password_expired';
    detail?: string;
}

/**
 * Response for POST /users/management/ (Signup)
 */
export interface SignupResponse {
    data: UserProfile;
}

/**
 * Response for GET /users/management/me/
 */
export interface MeResponse {
    data: UserProfile;
}
