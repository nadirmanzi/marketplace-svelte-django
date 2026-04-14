import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		hmr: {
			clientPort: 80
		},
		// If you're using a VM or certain Linux setups, polling might be needed.
		watch: { usePolling: true }
	}
});
