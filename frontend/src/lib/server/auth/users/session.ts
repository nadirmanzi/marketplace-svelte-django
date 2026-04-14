import { redirect } from "@sveltejs/kit";

export const getSession = (locals: App.Locals, url: URL) => {
    if (!locals.is_authenticated || !locals.user) {
        redirect(302, `/auth/login?next=${encodeURIComponent(url.pathname)}`);
    }
    return locals.user;
};

export const guardAuth = (locals: App.Locals, url: URL) => {
    if (locals.is_authenticated) {
        const next = sanitizeNext(url.searchParams.get('next'));
        redirect(302, next);
    }
};

export const sanitizeNext = (next: string | null): string => {
    if (!next) return '/';
    if (!next.startsWith('/') || next.startsWith('//')) return '/';
    return next;
};