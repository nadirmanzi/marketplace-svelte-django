import { z } from 'zod'

export const login_schema = z.object({
    email: z.email({ error: 'Email provided is invalid!' }).min(1, { error: "An email address is required!" }),
    password: z.string().min(1, { error: 'A password is required!' })
})

export const signup_schema = z.object({
    full_name: z.string().min(3, { error: 'At least 3 characters required!' }),
    email: z.email({ error: 'Email provided is invalid!' }).min(1, { error: 'An email address is required!' }),
    password: z.string().min(8, { error: 'Password must be at least 8 characters!' }),
    confirm_password: z.string().min(1, { error: 'Please confirm your password!' })  // ← must be here inside z.object()
}).superRefine((data, ctx) => {
    if (data.password !== data.confirm_password) {
        ctx.addIssue({
            code: 'custom',
            message: 'Passwords do not match!',
            path: ['confirm_password']
        });
    }
});