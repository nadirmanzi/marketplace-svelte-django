import { cubicOut } from 'svelte/easing';

export function slideFade(
	node: HTMLElement,
	{ delay = 0, duration = 400, easing = cubicOut, axis = 'y' }: any = {}
) {
	const style = getComputedStyle(node);
	const opacity = +style.opacity;
	const primary_property = axis === 'y' ? 'height' : 'width';
	const primary_property_value = parseFloat(style[primary_property as any]) || 0;

	const padding_a_camel = axis === 'y' ? 'paddingTop' : 'paddingLeft';
	const padding_b_camel = axis === 'y' ? 'paddingBottom' : 'paddingRight';
	const margin_a_camel = axis === 'y' ? 'marginTop' : 'marginLeft';
	const margin_b_camel = axis === 'y' ? 'marginBottom' : 'marginRight';
	const border_a_camel = axis === 'y' ? 'borderTopWidth' : 'borderLeftWidth';
	const border_b_camel = axis === 'y' ? 'borderBottomWidth' : 'borderRightWidth';

	const padding_a_value = parseFloat(style[padding_a_camel as any]) || 0;
	const padding_b_value = parseFloat(style[padding_b_camel as any]) || 0;
	const margin_a_value = parseFloat(style[margin_a_camel as any]) || 0;
	const margin_b_value = parseFloat(style[margin_b_camel as any]) || 0;
	const border_a_value = parseFloat(style[border_a_camel as any]) || 0;
	const border_b_value = parseFloat(style[border_b_camel as any]) || 0;

	const padding_a_kebab = axis === 'y' ? 'padding-top' : 'padding-left';
	const padding_b_kebab = axis === 'y' ? 'padding-bottom' : 'padding-right';
	const margin_a_kebab = axis === 'y' ? 'margin-top' : 'margin-left';
	const margin_b_kebab = axis === 'y' ? 'margin-bottom' : 'margin-right';
	const border_a_kebab = axis === 'y' ? 'border-top-width' : 'border-left-width';
	const border_b_kebab = axis === 'y' ? 'border-bottom-width' : 'border-right-width';

	return {
		delay,
		duration,
		easing,
		css: (t: number) =>
			`overflow: hidden;` +
			`opacity: ${t * opacity};` +
			`${primary_property}: ${t * primary_property_value}px;` +
			`${padding_a_kebab}: ${t * padding_a_value}px;` +
			`${padding_b_kebab}: ${t * padding_b_value}px;` +
			`${margin_a_kebab}: ${t * margin_a_value}px;` +
			`${margin_b_kebab}: ${t * margin_b_value}px;` +
			`${border_a_kebab}: ${t * border_a_value}px;` +
			`${border_b_kebab}: ${t * border_b_value}px;`
	};
}
