"""
Tests for product enhancements: images, price fallback, and stock atomicity.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Category, Product, ProductVariant, ProductImage
from catalog.services.product_services import ProductService, VariantService
from catalog.services.category_services import CategoryService
from catalog.serializers import ProductVariantSummarySerializer

User = get_user_model()


class ProductEnhancementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.category = CategoryService.create_category(
            performed_by=self.user, name="Electronics"
        )

    def test_price_fallback(self):
        product = ProductService.create_product(
            performed_by=self.user,
            name="Laptop",
            base_price=Decimal("1000.00"),
            category=self.category.pk,
        )
        variant = VariantService.create_variant(
            product=product,
            performed_by=self.user,
            sku="LAPTOP-BASE",
            name="Base Model",
            price=None,  # Price is null
        )
        self.assertEqual(variant.effective_price, Decimal("1000.00"))

        # Serializer should also reflect this
        serializer = ProductVariantSummarySerializer(variant)
        self.assertEqual(Decimal(serializer.data["price"]), Decimal("1000.00"))

    def test_image_fallback(self):
        product = ProductService.create_product(
            performed_by=self.user,
            name="Phone",
            base_price=Decimal("500.00"),
        )
        # Add image to product
        img_content = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x03\x02\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b"
        img_file = SimpleUploadedFile("product.gif", img_content, content_type="image/gif")
        ProductImage.objects.create(product=product, image=img_file)

        variant = VariantService.create_variant(
            product=product,
            performed_by=self.user,
            sku="PHONE-RED",
            name="Red Phone",
            price=Decimal("550.00"),
        )

        # Variant has no images, should fallback
        serializer = ProductVariantSummarySerializer(variant)
        self.assertEqual(len(serializer.data["images"]), 1)
        image_url = serializer.data["images"][0]["image"]
        self.assertIn("product", image_url)
        self.assertIn(".gif", image_url)
        
        # Verify thumbnail exists in payload
        self.assertIn("thumbnail", serializer.data["images"][0])

        # Assign an image to variant
        var_img_file = SimpleUploadedFile("variant.gif", img_content, content_type="image/gif")
        ProductImage.objects.create(product=product, variant=variant, image=var_img_file)

        # Now should only show variant image
        serializer = ProductVariantSummarySerializer(variant)
        self.assertEqual(len(serializer.data["images"]), 1)
        var_image_url = serializer.data["images"][0]["image"]
        self.assertIn("variant", var_image_url)
        self.assertIn(".gif", var_image_url)

    def test_stock_adjustment_with_f(self):
        product = ProductService.create_product(
            performed_by=self.user, name="Stock Test", base_price=Decimal("10")
        )
        variant = VariantService.create_variant(
            product=product, performed_by=self.user, sku="STOCK-1", name="V1", 
            stock_quantity=10, price=Decimal("10")
        )

        # Adjust stock
        VariantService.adjust_stock(performed_by=self.user, variant=variant, quantity_delta=5)
        variant.refresh_from_db()
        self.assertEqual(variant.stock_quantity, 15)

        VariantService.adjust_stock(performed_by=self.user, variant=variant, quantity_delta=-10)
        variant.refresh_from_db()
        self.assertEqual(variant.stock_quantity, 5)

    def test_slug_collision_handling(self):
        # Category collision
        c1 = CategoryService.create_category(performed_by=self.user, name="Unique")
        c2 = CategoryService.create_category(performed_by=self.user, name="Unique")
        self.assertEqual(c1.slug, "unique")
        self.assertEqual(c2.slug, "unique-1")

        # Product collision
        p1 = ProductService.create_product(performed_by=self.user, name="Widget", base_price=Decimal("1"))
        p2 = ProductService.create_product(performed_by=self.user, name="Widget", base_price=Decimal("2"))
        self.assertEqual(p1.slug, "widget")
        self.assertEqual(p2.slug, "widget-1")
