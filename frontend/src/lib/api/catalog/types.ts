/**
 * Data models for the Catalog System.
 * Based on Catalog API Guide.
 */

export interface Category {
    category_id: string; // UUID
    name: string;
    slug: string;
    description: string | null;
    image: string | null;
    parent_id: string | null;
    depth: number;
    subcategory_count: number;
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
    options: string[] | null;
}

export interface CategoryAttribute {
    attribute: AttributeDefinition;
    order: number;
}

export interface ProductAttributeValue {
    attribute_id: string;
    name: string;
    slug: string;
    value: any; // String, Number, Boolean, or Array
}

export interface ProductVariant {
    variant_id: string;
    sku: string;
    name: string;
    price: string; // Decimal string
    in_stock: boolean;
    stock_quantity: number;
    images: string[];
    attributes: ProductAttributeValue[];
}

export interface ProductBlueprint {
    product_id: string;
    name: string;
    slug: string;
    description: string;
    base_price: string;
    is_published: boolean;
    category_id: string;
    category_name: string;
    images: string[];
    attributes: ProductAttributeValue[];
    variants: ProductVariant[];
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
