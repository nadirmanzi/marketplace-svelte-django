"""
URL configuration for the catalog app.

Routes:
- /catalog/categories/              -> Public category tree
- /catalog/categories/manage/       -> Staff category CRUD
- /catalog/products/                -> Public product listing
- /catalog/products/manage/         -> Owner/staff product CRUD
- /catalog/variants/manage/         -> Owner/staff variant CRUD
- /catalog/attributes/manage/       -> Staff attribute CRUD
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from catalog.views.category_views import (
    CategoryPublicViewSet,
    CategoryManagementViewSet,
)
from catalog.views.product_views import (
    ProductPublicViewSet,
    ProductManagementViewSet,
    VariantManagementViewSet,
)
from catalog.views.attribute_views import (
    AttributeViewSet,
    CategoryAttributeInfoView,
)
from catalog.views.discount_views import DiscountManagementViewSet

router = DefaultRouter()

# Categories
router.register(r"categories/manage", CategoryManagementViewSet, basename="category-manage")
router.register(r"categories", CategoryPublicViewSet, basename="category")

# Products
router.register(r"products/manage", ProductManagementViewSet, basename="product-manage")
router.register(r"products", ProductPublicViewSet, basename="product")

# Variants
router.register(r"variants/manage", VariantManagementViewSet, basename="variant-manage")

# Attributes
router.register(r"attributes/manage", AttributeViewSet, basename="attribute-manage")

# Discounts
router.register(r"discounts/manage", DiscountManagementViewSet, basename="discount-manage")

urlpatterns = [
    path("categories/<uuid:category_id>/attributes/", CategoryAttributeInfoView.as_view(), name="category-attributes"),
]

urlpatterns += router.urls