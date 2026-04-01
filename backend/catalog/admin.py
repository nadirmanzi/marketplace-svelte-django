"""
Django admin configuration for catalog models.

Registers Category, Product, and ProductVariant with history
tracking, custom forms, and inline variant editing.
"""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Category, Product, ProductVariant
from .forms import CategoryAdminForm


# ---------------------------------------------------------------------------
# Category Admin
# ---------------------------------------------------------------------------


@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    """Admin interface for Category with history tracking."""

    form = CategoryAdminForm

    list_display = ("name", "slug", "parent", "is_active", "created_at")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("category_id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("category_id", "name", "slug", "description", "image")}),
        ("Hierarchy", {"fields": ("parent",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ---------------------------------------------------------------------------
# Product Admin
# ---------------------------------------------------------------------------


class ProductVariantInline(admin.TabularInline):
    """Inline editor for variants within the Product admin page."""

    model = ProductVariant
    extra = 0
    readonly_fields = ("variant_id", "created_at", "updated_at")
    fields = ("variant_id", "sku", "name", "price", "stock_quantity", "is_active", "metadata")


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    """Admin interface for Product with inline variants."""

    list_display = ("name", "slug", "status", "base_price", "user", "category", "created_at")
    list_filter = ("status", "category")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-created_at",)
    readonly_fields = ("product_id", "created_at", "updated_at")
    raw_id_fields = ("user", "category")
    inlines = [ProductVariantInline]

    fieldsets = (
        (None, {"fields": ("product_id", "name", "slug", "description", "base_price")}),
        ("Relationships", {"fields": ("user", "category")}),
        ("Status", {"fields": ("status",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ---------------------------------------------------------------------------
# ProductVariant Admin
# ---------------------------------------------------------------------------


@admin.register(ProductVariant)
class ProductVariantAdmin(SimpleHistoryAdmin):
    """Standalone admin for ProductVariant with history tracking."""

    list_display = ("sku", "name", "product", "price", "stock_quantity", "is_active", "created_at")
    list_filter = ("is_active", "product")
    search_fields = ("sku", "name")
    ordering = ("name",)
    readonly_fields = ("variant_id", "created_at", "updated_at")
    raw_id_fields = ("product",)

    fieldsets = (
        (None, {"fields": ("variant_id", "product", "sku", "name")}),
        ("Pricing & Stock", {"fields": ("price", "stock_quantity")}),
        ("Attributes", {"fields": ("metadata",)}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
