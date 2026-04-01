"""
Integration tests for Category model, service layer, and API endpoints.

Covers:
- Model validation (circular references, auto-slug, depth)
- Service layer (create, update, deactivate cascade, activate)
- Public API (tree rendering, slug lookup)
- Management API (CRUD, lifecycle actions, permission enforcement)
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category
from catalog.services.category_services import CategoryService
from users.exceptions import ConflictError, ServiceValidationError, NotFoundError

User = get_user_model()


# ---------------------------------------------------------------------------
# Model Tests
# ---------------------------------------------------------------------------


class CategoryModelTests(TestCase):
    """Tests for Category model validation and behavior."""

    def test_auto_slug_from_name(self):
        """Slug is auto-generated from name if not provided."""
        cat = Category(name="Electronics & Gadgets")
        cat.save()
        self.assertEqual(cat.slug, "electronics-gadgets")

    def test_slug_collision_appends_suffix(self):
        """Duplicate names get unique slugs via numeric suffix."""
        cat1 = Category.objects.create(name="Books")
        cat2 = Category(name="Books")
        cat2.save()
        self.assertEqual(cat1.slug, "books")
        self.assertEqual(cat2.slug, "books-1")

    def test_self_parent_raises_validation_error(self):
        """A category cannot reference itself as parent."""
        cat = Category.objects.create(name="Root", slug="root")
        cat.parent = cat
        with self.assertRaises(ValidationError) as ctx:
            cat.full_clean()
        self.assertIn("parent", ctx.exception.message_dict)

    def test_circular_reference_detected(self):
        """Circular parent chains are detected and rejected."""
        a = Category.objects.create(name="A", slug="a")
        b = Category.objects.create(name="B", slug="b", parent=a)
        # Try to make A a child of B (circular: A -> B -> A)
        a.parent = b
        with self.assertRaises(ValidationError) as ctx:
            a.full_clean()
        self.assertIn("parent", ctx.exception.message_dict)

    def test_is_root_property(self):
        """is_root is True for categories without a parent."""
        root = Category.objects.create(name="Root", slug="root")
        child = Category.objects.create(name="Child", slug="child", parent=root)
        self.assertTrue(root.is_root)
        self.assertFalse(child.is_root)

    def test_depth_property(self):
        """depth returns correct nesting level."""
        root = Category.objects.create(name="L0", slug="l0")
        l1 = Category.objects.create(name="L1", slug="l1", parent=root)
        l2 = Category.objects.create(name="L2", slug="l2", parent=l1)
        self.assertEqual(root.depth, 0)
        self.assertEqual(l1.depth, 1)
        self.assertEqual(l2.depth, 2)

    def test_str_representation(self):
        """__str__ shows parent arrow for subcategories."""
        root = Category.objects.create(name="Electronics", slug="electronics")
        child = Category.objects.create(name="Phones", slug="phones", parent=root)
        self.assertEqual(str(root), "Electronics")
        self.assertEqual(str(child), "Electronics → Phones")


# ---------------------------------------------------------------------------
# Manager Tests
# ---------------------------------------------------------------------------


class CategoryManagerTests(TestCase):
    """Tests for CategoryManager custom querysets."""

    def setUp(self):
        self.active_root = Category.objects.create(name="Active Root", slug="active-root")
        self.inactive_root = Category.objects.create(
            name="Inactive Root", slug="inactive-root", is_active=False
        )
        self.child = Category.objects.create(
            name="Child", slug="child", parent=self.active_root
        )

    def test_active_filters_inactive(self):
        """active() excludes is_active=False."""
        qs = Category.objects.active()
        self.assertIn(self.active_root, qs)
        self.assertNotIn(self.inactive_root, qs)

    def test_roots_returns_only_top_level(self):
        """roots() returns categories without a parent."""
        qs = Category.objects.roots()
        self.assertIn(self.active_root, qs)
        self.assertIn(self.inactive_root, qs)
        self.assertNotIn(self.child, qs)

    def test_active_roots_combines_both(self):
        """active_roots() returns active categories without a parent."""
        qs = Category.objects.active_roots()
        self.assertIn(self.active_root, qs)
        self.assertNotIn(self.inactive_root, qs)
        self.assertNotIn(self.child, qs)


# ---------------------------------------------------------------------------
# Service Tests
# ---------------------------------------------------------------------------


class CategoryServiceTests(TestCase):
    """Tests for CategoryService business logic."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123!",
            full_name="Admin User",
        )

    def test_create_category(self):
        """Service creates a category with valid data."""
        cat = CategoryService.create_category(
            performed_by=self.admin,
            name="Electronics",
            slug="electronics",
        )
        self.assertEqual(cat.name, "Electronics")
        self.assertTrue(cat.is_active)
        self.assertIsNone(cat.parent)

    def test_create_with_parent(self):
        """Service resolves parent UUID and assigns it."""
        root = Category.objects.create(name="Root", slug="root")
        child = CategoryService.create_category(
            performed_by=self.admin,
            name="Child",
            slug="child",
            parent=root.category_id,
        )
        self.assertEqual(child.parent, root)

    def test_create_with_invalid_parent_raises(self):
        """Service raises NotFoundError for invalid parent UUID."""
        import uuid
        with self.assertRaises(NotFoundError):
            CategoryService.create_category(
                performed_by=self.admin,
                name="Orphan",
                slug="orphan",
                parent=uuid.uuid4(),
            )

    def test_update_category(self):
        """Service updates category fields."""
        cat = Category.objects.create(name="Old Name", slug="old-name")
        updated = CategoryService.update_category(
            performed_by=self.admin,
            category=cat,
            name="New Name",
        )
        self.assertEqual(updated.name, "New Name")

    def test_deactivate_cascades_to_children(self):
        """Deactivating a parent deactivates all descendants."""
        root = Category.objects.create(name="Root", slug="root")
        child = Category.objects.create(name="Child", slug="child", parent=root)
        grandchild = Category.objects.create(name="GC", slug="gc", parent=child)

        CategoryService.deactivate_category(
            performed_by=self.admin, category=root
        )

        root.refresh_from_db()
        child.refresh_from_db()
        grandchild.refresh_from_db()

        self.assertFalse(root.is_active)
        self.assertFalse(child.is_active)
        self.assertFalse(grandchild.is_active)

    def test_deactivate_already_inactive_raises(self):
        """Deactivating an already inactive category raises ConflictError."""
        cat = Category.objects.create(name="Inactive", slug="inactive", is_active=False)
        with self.assertRaises(ConflictError):
            CategoryService.deactivate_category(
                performed_by=self.admin, category=cat
            )

    def test_activate_category(self):
        """Activating an inactive category sets is_active=True."""
        cat = Category.objects.create(name="Inactive", slug="inactive", is_active=False)
        result = CategoryService.activate_category(
            performed_by=self.admin, category=cat
        )
        self.assertTrue(result.is_active)

    def test_activate_already_active_raises(self):
        """Activating an already active category raises ConflictError."""
        cat = Category.objects.create(name="Active", slug="active")
        with self.assertRaises(ConflictError):
            CategoryService.activate_category(
                performed_by=self.admin, category=cat
            )


# ---------------------------------------------------------------------------
# Public API Tests
# ---------------------------------------------------------------------------


class CategoryPublicAPITests(APITestCase):
    """Tests for the public (unauthenticated) category tree API."""

    def setUp(self):
        self.root1 = Category.objects.create(name="Electronics", slug="electronics")
        self.root2 = Category.objects.create(name="Books", slug="books")
        self.child1 = Category.objects.create(
            name="Phones", slug="phones", parent=self.root1
        )
        self.inactive = Category.objects.create(
            name="Discontinued", slug="discontinued", is_active=False
        )

    def test_list_returns_active_roots_only(self):
        """Public list returns only active root categories."""
        url = reverse("category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        # Unwrap standardized response if wrapped
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        slugs = [c["slug"] for c in data]
        self.assertIn("electronics", slugs)
        self.assertIn("books", slugs)
        self.assertNotIn("discontinued", slugs)
        self.assertNotIn("phones", slugs)  # It's a child, not a root

    def test_list_includes_nested_children(self):
        """Root categories include their active children in the response."""
        url = reverse("category-list")
        response = self.client.get(url)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        electronics = next(c for c in data if c["slug"] == "electronics")
        self.assertEqual(len(electronics["children"]), 1)
        self.assertEqual(electronics["children"][0]["slug"], "phones")

    def test_retrieve_by_slug(self):
        """Retrieve a category by its slug."""
        url = reverse("category-detail", kwargs={"slug": "electronics"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        self.assertEqual(data["slug"], "electronics")

    def test_retrieve_inactive_returns_404(self):
        """Inactive categories are not publicly accessible."""
        url = reverse("category-detail", kwargs={"slug": "discontinued"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Management API Tests
# ---------------------------------------------------------------------------


class CategoryManagementAPITests(APITestCase):
    """Tests for the staff-only category management API."""

    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="admin123!",
            full_name="Admin User",
        )
        self.regular_user = User.objects.create_user(
            email="user@test.com",
            password="user123!",
            full_name="Regular User",
        )
        self.root = Category.objects.create(name="Electronics", slug="electronics")

    def test_create_category_as_admin(self):
        """Admin can create a new category."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("category-manage-list")
        response = self.client.post(url, {
            "name": "Fashion",
            "slug": "fashion",
            "description": "Clothing and accessories",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_category_as_regular_user_denied(self):
        """Non-staff users cannot create categories."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse("category-manage-list")
        response = self.client.post(url, {"name": "Hacks"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_create_denied(self):
        """Unauthenticated requests cannot create categories."""
        url = reverse("category-manage-list")
        response = self.client.post(url, {"name": "Hacks"})
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_update_category(self):
        """Admin can update a category."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("category-manage-detail", kwargs={"pk": self.root.pk})
        response = self.client.patch(url, {"name": "Tech"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_deactivate_endpoint(self):
        """Admin can deactivate a category via the action endpoint."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("category-manage-deactivate", kwargs={"pk": self.root.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.root.refresh_from_db()
        self.assertFalse(self.root.is_active)

    def test_activate_endpoint(self):
        """Admin can activate an inactive category."""
        self.root.is_active = False
        self.root.save(update_fields=["is_active"])

        self.client.force_authenticate(user=self.admin)
        url = reverse("category-manage-activate", kwargs={"pk": self.root.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.root.refresh_from_db()
        self.assertTrue(self.root.is_active)

    def test_list_includes_inactive_for_admin(self):
        """Admin list shows all categories including inactive."""
        Category.objects.create(name="Hidden", slug="hidden", is_active=False)

        self.client.force_authenticate(user=self.admin)
        url = reverse("category-manage-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if isinstance(data, dict) and "items" in data:
            data = data["items"]

        slugs = [c["slug"] for c in data]
        self.assertIn("hidden", slugs)
