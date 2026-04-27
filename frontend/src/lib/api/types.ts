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
 * Minimal user representation embedded in other resources.
 */
export interface EmbeddedUser {
    user_id: string;
    email: string;
    full_name: string;
}

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
export interface SignupResponse {
    user: EmbeddedUser;
}

/**
 * Response for GET /users/management/me/
 */
export interface MeResponse {
    user: UserProfile;
}

/** 
 * Catalog Categories Responses
 */
export interface CategoryTreeResponse {
    data: {
        categories: any[]; // Recursive structure
    }
}

export interface CategoryDetailResponse {
    category: any;
}

/**
 * Catalog Product Responses
 */
export interface ProductListResponse {
    products: any[];
}

export interface ProductDetailResponse {
    product: any;
}

/**
 * Catalog Variant Responses
 */
export interface VariantDetailResponse {
    variant: any;
}
