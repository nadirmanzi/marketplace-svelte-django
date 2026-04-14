"""
Tests for the hierarchical attribute system.
Verifies inheritance, strict validation, and variant overrides.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from catalog.models import Category, Product, ProductVariant, Attribute, AttributeOption
from catalog.services.product_services import ProductService, VariantService
from catalog.services.attribute_services import AttributeService
from users.exceptions import ServiceValidationError

User = get_user_model()


class AttributeSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="admin@test.com", password="pass123!", full_name="Admin", is_staff=True
        )
        
        # Hierarchy: Electronics -> Phone
        self.electronics = Category.objects.create(name="Electronics", slug="electronics")
        self.phone_cat = Category.objects.create(name="Phone", slug="phone", parent=self.electronics)
        
        # Attributes
        self.warranty = AttributeService.create_attribute(
            name="Warranty", slug="warranty", input_type=Attribute.InputType.NUMBER, unit="months", is_required=True
        )
        self.ram = AttributeService.create_attribute(
            name="RAM", slug="ram", input_type=Attribute.InputType.SELECT, is_required=True,
            options=["8GB", "16GB"]
        )
        
        # Assign Warranty to Electronics (Parent)
        AttributeService.assign_to_category(self.electronics.pk, self.warranty.pk)
        
        # Assign RAM to Phone (Child)
        AttributeService.assign_to_category(self.phone_cat.pk, self.ram.pk)

    def test_attribute_inheritance(self):
        """Verify that Phone inherits Warranty from Electronics."""
        attrs = AttributeService.get_attributes_for_category(self.phone_cat)
        slugs = [a.slug for a in attrs]
        self.assertIn("warranty", slugs)
        self.assertIn("ram", slugs)
        
        # Electronics should NOT have RAM
        elec_attrs = AttributeService.get_attributes_for_category(self.electronics)
        elec_slugs = [a.slug for a in elec_attrs]
        self.assertIn("warranty", elec_slugs)
        self.assertNotIn("ram", elec_slugs)

    def test_strict_validation_on_product_creation(self):
        """Verify that missing required attributes (including inherited) blocks creation."""
        
        # Missing both Warranty and RAM
        with self.assertRaises(ServiceValidationError) as cm:
            ProductService.create_product(
                performed_by=self.user,
                name="iPhone 15",
                base_price=Decimal("999.00"),
                category=self.phone_cat.pk,
                attributes={}
            )
        self.assertIn("Missing required attribute", str(cm.exception))

        # Provided RAM but missing Warranty (inherited)
        with self.assertRaises(ServiceValidationError) as cm:
            ProductService.create_product(
                performed_by=self.user,
                name="iPhone 15",
                base_price=Decimal("999.00"),
                category=self.phone_cat.pk,
                attributes={"ram": ["8GB"]}
            )
        self.assertIn("Warranty", str(cm.exception))

        # Correct creation
        product = ProductService.create_product(
            performed_by=self.user,
            name="iPhone 15",
            base_price=Decimal("999.00"),
            category=self.phone_cat.pk,
            attributes={"warranty": 24, "ram": ["16GB"]}
        )
        self.assertEqual(product.attribute_values.count(), 2)

    def test_variant_attribute_override(self):
        """Verify that variants can have their own specific attributes."""
        product = ProductService.create_product(
            performed_by=self.user,
            name="Galaxy S24",
            base_price=Decimal("800.00"),
            category=self.phone_cat.pk,
            attributes={"warranty": 12, "ram": ["8GB"]}
        )
        
        # Variant inherits 'warranty' and 'ram' from product blueprint conceptually, 
        # but we can also set variant-specific attributes like 'Color' if defined.
        
        color_attr = AttributeService.create_attribute(
            name="Color", slug="color", input_type=Attribute.InputType.TEXT
        )
        AttributeService.assign_to_category(self.phone_cat.pk, color_attr.pk)
        
        variant = VariantService.create_variant(
            performed_by=self.user,
            product=product,
            sku="S24-BLUE",
            name="Blue Edition",
            price=Decimal("850.00"),
            attributes={"color": "Ocean Blue"}
        )
        
        self.assertEqual(variant.attribute_values.count(), 1)
        self.assertEqual(variant.attribute_values.first().value_text, "Ocean Blue")

    def test_invalid_type_validation(self):
        """Verify that numeric attributes reject strings."""
        with self.assertRaises(ServiceValidationError) as cm:
            ProductService.create_product(
                performed_by=self.user,
                name="Invalid Product",
                base_price=Decimal("10.00"),
                category=self.phone_cat.pk,
                attributes={"warranty": "two years", "ram": ["8GB"]}
            )
        self.assertIn("must be a number", str(cm.exception))
