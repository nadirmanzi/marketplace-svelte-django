"""
Product & Variant API views: public browsing and owner/staff management.

Public endpoints (ProductPublicViewSet):
- GET  /catalog/products/              -> list published products with active variants
- GET  /catalog/products/{slug}/       -> single product detail with variants

Management endpoints (ProductManagementViewSet):
- GET/POST      /catalog/products/manage/          -> list/create products
- GET/PUT/PATCH /catalog/products/manage/{pk}/      -> retrieve/update product
- POST          /catalog/products/manage/{pk}/archive/  -> archive (cascade)
- POST          /catalog/products/manage/{pk}/publish/  -> publish

Variant Management (VariantManagementViewSet):
- GET/POST      /catalog/variants/manage/          -> list/create variants
- GET/PUT/PATCH /catalog/variants/manage/{pk}/      -> retrieve/update variant
- POST          /catalog/variants/manage/{pk}/adjust-stock/  -> locked stock adjustment
- POST          /catalog/variants/manage/{pk}/deactivate/    -> deactivate
- POST          /catalog/variants/manage/{pk}/activate/      -> activate
"""

import logging

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from catalog.models import Product, ProductVariant
from catalog.serializers import (
    ProductSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
    ProductVariantSerializer,
    ProductVariantWriteSerializer,
    StockAdjustmentSerializer,
)
from catalog.filters import ProductFilter, ProductVariantFilter
from catalog.permissions import IsOwnerOrStaff
from catalog.services.product_services import ProductService, VariantService


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public Product ViewSet
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        summary="List Published Products",
        description="Returns published products with their active variants embedded.",
        responses={200: ProductDetailSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Product by Slug",
        description="Retrieve a published product and its active variants by slug.",
        responses={200: ProductDetailSerializer},
    ),
)
class ProductPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Public read-only access to published products.

    - list: Returns published products with nested active variants.
    - retrieve: Returns a single product by slug with its variants.
    """

    permission_classes = [AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    def get_queryset(self):
        return (
            Product.objects
            .published()
            .select_related("category", "user")
            .prefetch_related("variants")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"products": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """Get a single published product by slug."""
        try:
            product = (
                Product.objects
                .published()
                .select_related("category", "user")
                .get(slug=kwargs["slug"])
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(product)
        return Response({"product": serializer.data})


# ---------------------------------------------------------------------------
# Product Management ViewSet (owner or staff)
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        summary="List All Products (Admin/Owner)",
        description="Filterable list of all products including archived.",
    ),
    retrieve=extend_schema(
        summary="Get Product Detail (Admin/Owner)",
        description="Retrieve full product details by UUID.",
    ),
    create=extend_schema(
        summary="Create Product",
        description="Create a new product blueprint.",
        request=ProductWriteSerializer,
        responses={201: ProductSerializer},
    ),
    update=extend_schema(
        summary="Update Product",
        description="Full update of a product blueprint.",
        request=ProductWriteSerializer,
        responses={200: ProductSerializer},
    ),
    partial_update=extend_schema(
        summary="Partial Update Product",
        description="Partial update of a product blueprint.",
        request=ProductWriteSerializer,
        responses={200: ProductSerializer},
    ),
)
class ProductManagementViewSet(viewsets.ModelViewSet):
    """
    Owner/staff CRUD and lifecycle actions for products.

    Permission: authenticated owner, staff, or superuser.
    """

    permission_classes = [IsOwnerOrStaff]
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    lookup_field = "pk"

    def get_queryset(self):
        """Staff sees all; regular users see only their own."""
        qs = Product.objects.all().select_related("category", "user")
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"products": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        assigned_user = data.pop("user", None)
        
        if request.user.is_staff or request.user.is_superuser:
            data["user_id"] = assigned_user or request.user.pk
        else:
            data["user_id"] = request.user.pk

        product = ProductService.create_product(
            performed_by=request.user,
            **data,
        )
        return Response(
            {"product": ProductSerializer(product).data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = ProductWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        assigned_user = data.pop("user", None)
        
        if assigned_user and (request.user.is_staff or request.user.is_superuser):
            data["user_id"] = assigned_user

        product = ProductService.update_product(
            performed_by=request.user,
            product=product,
            **data,
        )
        return Response({"product": ProductSerializer(product).data})

    def partial_update(self, request, *args, **kwargs):
        product = self.get_object()
        serializer = ProductWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        if "user" in data:
            assigned_user = data.pop("user")
            if assigned_user and (request.user.is_staff or request.user.is_superuser):
                data["user_id"] = assigned_user

        product = ProductService.update_product(
            performed_by=request.user,
            product=product,
            **data,
        )
        return Response({"product": ProductSerializer(product).data})

    @extend_schema(
        summary="Archive Product",
        description="Archive a product and deactivate all its variants.",
        request=None,
        responses={200: ProductSerializer},
    )
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        product = self.get_object()
        product = ProductService.archive_product(
            performed_by=request.user, product=product
        )
        return Response({"product": ProductSerializer(product).data})

    @extend_schema(
        summary="Publish Product",
        description="Publish/un-archive a product.",
        request=None,
        responses={200: ProductSerializer},
    )
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        product = self.get_object()
        product = ProductService.publish_product(
            performed_by=request.user, product=product
        )
        return Response({"product": ProductSerializer(product).data})


# ---------------------------------------------------------------------------
# Variant Management ViewSet (owner or staff)
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        summary="List All Variants (Admin/Owner)",
        description="Filterable list of all variants.",
    ),
    retrieve=extend_schema(
        summary="Get Variant Detail (Admin/Owner)",
        description="Retrieve full variant details by UUID.",
    ),
    create=extend_schema(
        summary="Create Variant",
        description="Create a new variant under a product.",
        request=ProductVariantWriteSerializer,
        responses={201: ProductVariantSerializer},
    ),
    update=extend_schema(
        summary="Update Variant",
        description="Full update of a variant (excluding stock — use adjust-stock).",
        request=ProductVariantWriteSerializer,
        responses={200: ProductVariantSerializer},
    ),
    partial_update=extend_schema(
        summary="Partial Update Variant",
        description="Partial update of a variant.",
        request=ProductVariantWriteSerializer,
        responses={200: ProductVariantSerializer},
    ),
)
class VariantManagementViewSet(viewsets.ModelViewSet):
    """
    Owner/staff CRUD and lifecycle actions for product variants.

    Permission: authenticated owner (of parent product), staff, or superuser.
    """

    permission_classes = [IsOwnerOrStaff]
    serializer_class = ProductVariantSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductVariantFilter
    lookup_field = "pk"

    def get_queryset(self):
        """Staff sees all; regular users see only variants of their products."""
        qs = ProductVariant.objects.all().select_related("product", "product__user")
        if self.request.user.is_staff or self.request.user.is_superuser:
            return qs
        return qs.filter(product__user=self.request.user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductVariantWriteSerializer
        return ProductVariantSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"variants": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = ProductVariantWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        product_id = data.pop("product", None)
        if not product_id:
            return Response(
                {"detail": "Product UUID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify ownership for non-staff
        if not (request.user.is_staff or request.user.is_superuser):
            if product.user_id != request.user.pk:
                return Response(
                    {"detail": "You do not own this product."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        variant = VariantService.create_variant(
            performed_by=request.user,
            product=product,
            **data,
        )
        return Response(
            {"variant": ProductVariantSerializer(variant).data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        variant = self.get_object()
        serializer = ProductVariantWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("product", None)  # Cannot re-assign product

        variant = VariantService.update_variant(
            performed_by=request.user, variant=variant, **data
        )
        return Response({"variant": ProductVariantSerializer(variant).data})

    def partial_update(self, request, *args, **kwargs):
        variant = self.get_object()
        serializer = ProductVariantWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("product", None)

        variant = VariantService.update_variant(
            performed_by=request.user, variant=variant, **data
        )
        return Response({"variant": ProductVariantSerializer(variant).data})

    @extend_schema(
        summary="Adjust Stock",
        description="Atomically adjust variant stock with row-level locking.",
        request=StockAdjustmentSerializer,
        responses={200: ProductVariantSerializer},
    )
    @action(detail=True, methods=["post"], url_path="adjust-stock")
    def adjust_stock(self, request, pk=None):
        variant = self.get_object()
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant = VariantService.adjust_stock(
            performed_by=request.user,
            variant=variant,
            quantity_delta=serializer.validated_data["quantity_delta"],
        )
        return Response({"variant": ProductVariantSerializer(variant).data})

    @extend_schema(
        summary="Deactivate Variant",
        description="Deactivate a variant.",
        request=None,
        responses={200: ProductVariantSerializer},
    )
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        variant = self.get_object()
        variant = VariantService.deactivate_variant(
            performed_by=request.user, variant=variant
        )
        return Response({"variant": ProductVariantSerializer(variant).data})

    @extend_schema(
        summary="Activate Variant",
        description="Activate a variant.",
        request=None,
        responses={200: ProductVariantSerializer},
    )
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        variant = self.get_object()
        variant = VariantService.activate_variant(
            performed_by=request.user, variant=variant
        )
        return Response({"variant": ProductVariantSerializer(variant).data})
