/**
 * Data models for the Catalog System.
 * Based on Catalog API Guide & FinalPricingService.
 */
import type { EmbeddedUser } from '../types';

export interface DiscountInfo {
	discount_id: string;
	name: string;
	type: 'percentage' | 'fixed_amount';
	value: string; // Decimal
	scope: 'variant' | 'product' | 'category';
}

export interface Category {
	category_id: string; // UUID
	name: string;
	slug: string;
	description: string | null;
	image: string | null;
	parent_id: string | null;
	depth: number;
	subcategory_count: number;
	discount: DiscountInfo | null;
}

export interface CategoryResponse {
	category: Category;
}

export interface CategoryNode extends Category {
	children: CategoryNode[];
}

export interface AttributeDefinition {
	attribute_id: string;
	name: string;
	slug: string;
	input_type: 'text' | 'number' | 'boolean' | 'select' | 'multi-select';
	unit: string | null;
	options: { option_id: string; value: string }[] | null;
}

export interface CategoryAttribute {
	attribute: AttributeDefinition;
	order: number;
}

export interface ProductAttributeValue {
	attribute_id: string;
	name: string;
	slug: string;
	input_type: string;
	unit: string | null;
	value: any; // String, Number, Boolean, or Array
}

export interface ProductVariant {
	variant_id: string;
	sku: string;
	name: string;
	base_price: string;
	final_price: string;
	in_stock: boolean;
	stock_quantity: number;
	images: { image_id: number; image: string; thumbnail: string; alt_text: string }[];
	attributes: ProductAttributeValue[];
	discount: DiscountInfo | null;
}

export interface ProductBlueprint {
	product_id: string;
	name: string;
	slug: string;
	description: string;
	base_price: string;
	final_price: string;
	is_published: boolean;
	category_id: string;
	category_name: string;
	images: { image_id: number; image: string; thumbnail: string; alt_text: string }[];
	attributes: ProductAttributeValue[];
	variants: ProductVariant[];
	discount: DiscountInfo | null;
	user: EmbeddedUser;
	created_at: string;
	updated_at: string;
}

export interface ProductFilter {
	category?: string; // UUID
	min_price?: number | string;
	max_price?: number | string;
	name?: string;
	page?: number;
	page_size?: number;
}
