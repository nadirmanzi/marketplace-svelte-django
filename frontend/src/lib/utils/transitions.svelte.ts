import { cubicOut } from 'svelte/easing';

/**
 * @param {Element} node
 * @param {{ 
 * delay?: number, 
 * duration?: number, 
 * easing?: (t: number) => number, 
 * baseScale?: number,  // What it scales from (e.g., 0.8)
 * baseOpacity?: number // What it fades from (e.g., 0)
 * }} params
 */
export function fadeScale(node, {
	delay = 0,
	duration = 400,
	easing = cubicOut,
	baseScale = 0.9,
	baseOpacity = 0
}) {
	const style = getComputedStyle(node);
	const targetOpacity = +style.opacity;
	const transform = style.transform === 'none' ? '' : style.transform;

	return {
		delay,
		duration,
		easing,
		// t: 0.0 -> 1.0 (intro)
		// t: 1.0 -> 0.0 (outro)
		css: (t: number) => {
			const scale = baseScale + (1 - baseScale) * t;
			const opacity = baseOpacity + (targetOpacity - baseOpacity) * t;

			return `
                transform: ${transform} scale(${scale});
                opacity: ${opacity};
            `;
		}
	};
}