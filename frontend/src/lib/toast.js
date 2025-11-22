import { writable } from 'svelte/store'

export const toasts = writable([]);

export function showToast(message, type="info", duration=3000) {
    const id = Math.random().toString(36)
    
    toasts.update(all => [...all, { id, message, type }]);

    setTimeout(() => {
        toasts.update(all => all.filter(toast => toast.id !== id));
    }, duration);
}