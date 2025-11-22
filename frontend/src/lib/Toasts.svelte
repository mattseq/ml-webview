<script>
    import { toasts } from './toast.js';
    import { fly, fade } from 'svelte/transition';
</script>

<div class="toast-container">
    {#each $toasts as toast (toast.id)}
        <div 
            class="toast {toast.type}"
            transition:fly={{ y: -20, duration: 300 }}
        >
            {toast.message}
        </div>
    {/each}
</div>

<style>
    .toast-container {
        position: fixed;
        top: 1rem;
        right: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        z-index: 1000;
    }

    .toast {
        padding: 1rem;
        border-radius: 0.25rem;
        color: white;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }

    .toast.info {
        background-color: #2196F3;
    }

    .toast.success {
        background-color: #4CAF50;
    }

    .toast.error {
        background-color: #F44336;
    }
</style>