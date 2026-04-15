"""
Catalog models package.

Split into focused model modules to keep the domain easier to maintain.
"""

from .category import Category
from .discount import Discount
from .product import Product
from .product_variant import ProductVariant
from .supporting import (
    Attribute,
    AttributeOption,
    CategoryAttribute,
    ProductAttributeValue,
    ProductImage,
    VariantAttributeValue,
)

__all__ = [
    "Category",
    "Product",
    "ProductVariant",
    "Discount",
    "ProductImage",
    "Attribute",
    "AttributeOption",
    "CategoryAttribute",
    "ProductAttributeValue",
    "VariantAttributeValue",
]
