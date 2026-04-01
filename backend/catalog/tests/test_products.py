"""
Integration tests for Product and ProductVariant models, services, and API.

Covers:
- Model validation (price, status, slug, str repr)
- Service layer (create, update, archive, publish, stock locking)
- Public API (only published products, only active variants)
- Management API (CRUD, lifecycle, permission enforcement)
- Stock adjustment with row-level locking
"""

from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product, ProductVariant
from catalog.services.product_services import ProductService, VariantService
from users.exceptions import ConflictError, ServiceValidationError, NotFoundError

User = get_user_model()


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------


class ProductModelTests(TestCase):
    """Tests for Product model validation and behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")

    def test_auto_slug_from_name(self):
        product = Product(
            name="Wireless Headphones",
            base_price=Decimal("49.99"),
            user=self.user,
            category=self.category,
        )
        product.save()
        self.assertEqual(product.slug, "wireless-headphones")

    def test_slug_collision(self):
        Product.objects.create(
            name="Phone", slug="phone", base_price=Decimal("999"), user=self.user
        )
        p2 = Product(name="Phone", base_price=Decimal("899"), user=self.user)
        p2.save()
        self.assertEqual(p2.slug, "phone-1")

    def test_negative_price_rejected(self):
        product = Product(
            name="Bad", base_price=Decimal("-10"), user=self.user
        )
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_str_representation(self):
        product = Product.objects.create(
            name="Widget", slug="widget", base_price=Decimal("10"), user=self.user
        )
        self.assertEqual(str(product), "Widget")

    def test_is_published_property(self):
        product = Product.objects.create(
            name="P", slug="p", base_price=Decimal("10"),
            user=self.user, status=Product.Status.PUBLISHED
        )
        self.assertTrue(product.is_published)
        product.status = Product.Status.ARCHIVED
        self.assertFalse(product.is_published)


class ProductVariantModelTests(TestCase):
    """Tests for ProductVariant model validation and behavior."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.product = Product.objects.create(
            name="Shoes", slug="shoes", base_price=Decimal("99.99"), user=self.user
        )

    def test_negative_price_rejected(self):
        variant = ProductVariant(
            product=self.product, sku="BAD-SKU", name="Bad",
            price=Decimal("-5"),
        )
        with self.assertRaises(ValidationError):
            variant.full_clean()

    def test_in_stock_property(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="S-001", name="Size 10",
            price=Decimal("99.99"), stock_quantity=5,
        )
        self.assertTrue(variant.in_stock)
        variant.stock_quantity = 0
        self.assertFalse(variant.in_stock)

    def test_str_representation(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="S-002", name="Size 11",
            price=Decimal("99.99"),
        )
        self.assertEqual(str(variant), "Shoes — Size 11")


# ---------------------------------------------------------------------------
# Service Tests
# ---------------------------------------------------------------------------


class ProductServiceTests(TestCase):
    """Tests for ProductService business logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")

    def test_create_product(self):
        product = ProductService.create_product(
            performed_by=self.user,
            name="Laptop",
            base_price=Decimal("1299.99"),
            category=self.category.pk,
        )
        self.assertEqual(product.name, "Laptop")
        self.assertEqual(product.user, self.user)
        self.assertEqual(product.category, self.category)
        self.assertTrue(product.is_published)

    def test_create_with_invalid_category(self):
        import uuid
        with self.assertRaises(NotFoundError):
            ProductService.create_product(
                performed_by=self.user,
                name="Bad",
                base_price=Decimal("10"),
                category=uuid.uuid4(),
            )

    def test_update_product(self):
        product = Product.objects.create(
            name="Old", slug="old", base_price=Decimal("10"), user=self.user
        )
        updated = ProductService.update_product(
            performed_by=self.user, product=product, name="New Name"
        )
        self.assertEqual(updated.name, "New Name")

    def test_archive_product_cascades(self):
        product = Product.objects.create(
            name="P", slug="p", base_price=Decimal("10"), user=self.user
        )
        v1 = ProductVariant.objects.create(
            product=product, sku="V1", name="V1",
            price=Decimal("10"), is_active=True,
        )
        v2 = ProductVariant.objects.create(
            product=product, sku="V2", name="V2",
            price=Decimal("20"), is_active=True,
        )

        ProductService.archive_product(performed_by=self.user, product=product)

        product.refresh_from_db()
        v1.refresh_from_db()
        v2.refresh_from_db()

        self.assertEqual(product.status, Product.Status.ARCHIVED)
        self.assertFalse(v1.is_active)
        self.assertFalse(v2.is_active)

    def test_archive_already_archived_raises(self):
        product = Product.objects.create(
            name="P", slug="p", base_price=Decimal("10"),
            user=self.user, status=Product.Status.ARCHIVED,
        )
        with self.assertRaises(ConflictError):
            ProductService.archive_product(performed_by=self.user, product=product)

    def test_publish_product(self):
        product = Product.objects.create(
            name="P", slug="p", base_price=Decimal("10"),
            user=self.user, status=Product.Status.ARCHIVED,
        )
        result = ProductService.publish_product(performed_by=self.user, product=product)
        self.assertEqual(result.status, Product.Status.PUBLISHED)

    def test_publish_already_published_raises(self):
        product = Product.objects.create(
            name="P", slug="p", base_price=Decimal("10"), user=self.user,
        )
        with self.assertRaises(ConflictError):
            ProductService.publish_product(performed_by=self.user, product=product)


class VariantServiceTests(TestCase):
    """Tests for VariantService business logic."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.product = Product.objects.create(
            name="Shoes", slug="shoes", base_price=Decimal("99.99"), user=self.user
        )

    def test_create_variant(self):
        variant = VariantService.create_variant(
            performed_by=self.user,
            product=self.product,
            sku="SHOE-L-RED",
            name="Size L - Red",
            price=Decimal("109.99"),
            stock_quantity=50,
            metadata={"color": "red", "size": "L"},
        )
        self.assertEqual(variant.sku, "SHOE-L-RED")
        self.assertEqual(variant.stock_quantity, 50)
        self.assertEqual(variant.metadata["color"], "red")

    def test_update_variant_ignores_stock(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), stock_quantity=100,
        )
        updated = VariantService.update_variant(
            performed_by=self.user, variant=variant,
            name="Updated", stock_quantity=999,  # should be ignored
        )
        self.assertEqual(updated.name, "Updated")
        self.assertEqual(updated.stock_quantity, 100)  # unchanged

    def test_adjust_stock_add(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), stock_quantity=10,
        )
        result = VariantService.adjust_stock(
            performed_by=self.user, variant=variant, quantity_delta=5
        )
        self.assertEqual(result.stock_quantity, 15)

    def test_adjust_stock_subtract(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), stock_quantity=10,
        )
        result = VariantService.adjust_stock(
            performed_by=self.user, variant=variant, quantity_delta=-3
        )
        self.assertEqual(result.stock_quantity, 7)

    def test_adjust_stock_insufficient_raises(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), stock_quantity=5,
        )
        with self.assertRaises(ServiceValidationError):
            VariantService.adjust_stock(
                performed_by=self.user, variant=variant, quantity_delta=-10
            )

    def test_adjust_stock_zero_delta_raises(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), stock_quantity=5,
        )
        with self.assertRaises(ServiceValidationError):
            VariantService.adjust_stock(
                performed_by=self.user, variant=variant, quantity_delta=0
            )

    def test_deactivate_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), is_active=True,
        )
        result = VariantService.deactivate_variant(
            performed_by=self.user, variant=variant
        )
        self.assertFalse(result.is_active)

    def test_activate_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product, sku="V1", name="V1",
            price=Decimal("10"), is_active=False,
        )
        result = VariantService.activate_variant(
            performed_by=self.user, variant=variant
        )
        self.assertTrue(result.is_active)


# ---------------------------------------------------------------------------
# Public API Tests
# ---------------------------------------------------------------------------


class ProductPublicAPITests(APITestCase):
    """Tests for the public product listing API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="seller@test.com", password="pass123!", full_name="Seller"
        )
        self.published = Product.objects.create(
            name="Published", slug="published",
            base_price=Decimal("50"), user=self.user,
            status=Product.Status.PUBLISHED,
        )
        self.archived = Product.objects.create(
            name="Archived", slug="archived",
            base_price=Decimal("30"), user=self.user,
            status=Product.Status.ARCHIVED,
        )
        self.active_variant = ProductVariant.objects.create(
            product=self.published, sku="AV1", name="Active Var",
            price=Decimal("55"), stock_quantity=10, is_active=True,
        )
        self.inactive_variant = ProductVariant.objects.create(
            product=self.published, sku="IV1", name="Inactive Var",
            price=Decimal("60"), is_active=False,
        )

    def test_list_shows_published_only(self):
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        slugs = [p["slug"] for p in data]
        self.assertIn("published", slugs)
        self.assertNotIn("archived", slugs)

    def test_list_includes_active_variants_only(self):
        url = reverse("product-list")
        response = self.client.get(url)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        product = next(p for p in data if p["slug"] == "published")
        variant_skus = [v["sku"] for v in product["variants"]]
        self.assertIn("AV1", variant_skus)
        self.assertNotIn("IV1", variant_skus)

    def test_retrieve_by_slug(self):
        url = reverse("product-detail", kwargs={"slug": "published"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_archived_returns_404(self):
        url = reverse("product-detail", kwargs={"slug": "archived"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Management API Tests
# ---------------------------------------------------------------------------


class ProductManagementAPITests(APITestCase):
    """Tests for the owner/staff product management API."""

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="admin123!", full_name="Admin"
        )
        self.seller = User.objects.create_user(
            email="seller@test.com", password="seller123!", full_name="Seller"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="other123!", full_name="Other"
        )
        self.product = Product.objects.create(
            name="My Product", slug="my-product",
            base_price=Decimal("100"), user=self.seller,
        )

    def test_owner_can_create_product(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("product-manage-list")
        response = self.client.post(url, {
            "name": "New Product",
            "base_price": "59.99",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("product-manage-list")
        response = self.client.post(url, {
            "name": "Admin Product",
            "base_price": "99.99",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_create(self):
        url = reverse("product-manage-list")
        response = self.client.post(url, {"name": "Hacks", "base_price": "10"})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_owner_sees_own_products(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("product-manage-list")
        response = self.client.get(url)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["slug"], "my-product")

    def test_admin_sees_all_products(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("product-manage-list")
        response = self.client.get(url)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        self.assertGreaterEqual(len(data), 1)

    def test_archive_endpoint(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("product-manage-archive", kwargs={"pk": self.product.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.product.refresh_from_db()
        self.assertEqual(self.product.status, Product.Status.ARCHIVED)

    def test_publish_endpoint(self):
        self.product.status = Product.Status.ARCHIVED
        self.product.save(update_fields=["status"])

        self.client.force_authenticate(user=self.seller)
        url = reverse("product-manage-publish", kwargs={"pk": self.product.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class VariantManagementAPITests(APITestCase):
    """Tests for the owner/staff variant management API."""

    def setUp(self):
        cache.clear()
        self.seller = User.objects.create_user(
            email="seller@test.com", password="seller123!", full_name="Seller"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="admin123!", full_name="Admin"
        )
        self.product = Product.objects.create(
            name="Shoes", slug="shoes",
            base_price=Decimal("99.99"), user=self.seller,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="SHOE-L", name="Size L",
            price=Decimal("109.99"), stock_quantity=50,
        )

    def test_create_variant(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-list")
        response = self.client.post(url, {
            "product": str(self.product.pk),
            "sku": "SHOE-M",
            "name": "Size M",
            "price": "99.99",
            "stock_quantity": 25,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_adjust_stock_add(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-adjust-stock", kwargs={"pk": self.variant.pk})
        response = self.client.post(url, {"quantity_delta": 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 60)

    def test_adjust_stock_subtract(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-adjust-stock", kwargs={"pk": self.variant.pk})
        response = self.client.post(url, {"quantity_delta": -20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 30)

    def test_adjust_stock_insufficient(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-adjust-stock", kwargs={"pk": self.variant.pk})
        response = self.client.post(url, {"quantity_delta": -999})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])

    def test_deactivate_variant(self):
        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-deactivate", kwargs={"pk": self.variant.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.variant.refresh_from_db()
        self.assertFalse(self.variant.is_active)

    def test_activate_variant(self):
        self.variant.is_active = False
        self.variant.save(update_fields=["is_active"])

        self.client.force_authenticate(user=self.seller)
        url = reverse("variant-manage-activate", kwargs={"pk": self.variant.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.variant.refresh_from_db()
        self.assertTrue(self.variant.is_active)

    def test_other_user_cannot_create_variant(self):
        other = User.objects.create_user(
            email="other@test.com", password="other123!", full_name="Other"
        )
        self.client.force_authenticate(user=other)
        url = reverse("variant-manage-list")
        response = self.client.post(url, {
            "product": str(self.product.pk),
            "sku": "HACKED",
            "name": "Hacked Variant",
            "price": "1.00",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
