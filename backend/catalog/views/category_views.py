"""
Category API views: public browsing and staff management.

Public endpoints (CategoryPublicViewSet):
- GET  /catalog/categories/          -> list active root categories as nested tree
- GET  /catalog/categories/{slug}/   -> retrieve single category with its subtree

Management endpoints (CategoryManagementViewSet):
- GET    /catalog/categories/manage/              -> list all categories (flat, filterable)
- POST   /catalog/categories/manage/              -> create category
- GET    /catalog/categories/manage/{pk}/          -> retrieve category detail
- PUT    /catalog/categories/manage/{pk}/          -> full update
- PATCH  /catalog/categories/manage/{pk}/          -> partial update
- POST   /catalog/categories/manage/{pk}/deactivate/  -> deactivate (cascade)
- POST   /catalog/categories/manage/{pk}/activate/    -> activate
"""

import logging

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from catalog.models import Category
from catalog.serializers import (
    CategorySerializer,
    CategoryTreeSerializer,
    CategoryWriteSerializer,
)
from catalog.filters import CategoryFilter
from catalog.services.category_services import CategoryService


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public ViewSet (read-only, active categories only)
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        summary="List Categories (Flat)",
        description="Returns a flat list of active categories.",
        responses={200: CategorySerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get Category by Slug",
        description="Retrieve a single active category and its subtree by slug.",
        responses={200: CategoryTreeSerializer},
    ),
)
class CategoryPublicViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Public read-only access to categories.

    - list: Returns active categories as a flat list.
    - tree: Returns active root categories with nested children.
    - retrieve: Returns a single category by slug with its subtree.
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter

    def get_queryset(self):
        if self.action == "tree":
            return (
                Category.objects.active()
                .roots()
                .prefetch_related("subcategories")
                .order_by("name")
            )
        return Category.objects.active().select_related("parent").order_by("name")

    def get_serializer_class(self):
        if self.action in ("tree", "retrieve"):
            return CategoryTreeSerializer
        return CategorySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"categories": serializer.data})

    @extend_schema(
        summary="List Category Tree",
        description="Returns all active root categories with their nested subcategories.",
        responses={200: CategoryTreeSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"categories": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """Get a single category by slug (must be active)."""
        try:
            category = Category.objects.active().get(slug=kwargs["slug"])
        except Category.DoesNotExist:
            return Response(
                {"detail": "Category not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(category)
        return Response({"category": serializer.data})


# ---------------------------------------------------------------------------
# Management ViewSet (staff-only CRUD)
# ---------------------------------------------------------------------------


@extend_schema_view(
    list=extend_schema(
        summary="List All Categories (Admin)",
        description="Flat, filterable list of all categories including inactive.",
    ),
    retrieve=extend_schema(
        summary="Get Category Detail (Admin)",
        description="Retrieve full category details by UUID.",
    ),
    create=extend_schema(
        summary="Create Category",
        description="Create a new category. Requires staff or `can_manage_categories` permission.",
        request=CategoryWriteSerializer,
        responses={201: CategorySerializer},
    ),
    update=extend_schema(
        summary="Update Category",
        description="Full update of a category.",
        request=CategoryWriteSerializer,
        responses={200: CategorySerializer},
    ),
    partial_update=extend_schema(
        summary="Partial Update Category",
        description="Partial update of a category.",
        request=CategoryWriteSerializer,
        responses={200: CategorySerializer},
    ),
)
class CategoryManagementViewSet(viewsets.ModelViewSet):
    """
    Staff-only CRUD and lifecycle actions for categories.

    Permission model:
    - All actions require IsAdminUser (is_staff=True).
    - Superusers have unrestricted access.
    """

    permission_classes = [IsAdminUser]
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CategoryFilter
    lookup_field = "pk"

    def get_queryset(self):
        """Return all categories (including inactive) for management."""
        return Category.objects.all().select_related("parent").order_by("name")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({"categories": serializer.data})

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return CategoryWriteSerializer
        return CategorySerializer

    def create(self, request, *args, **kwargs):
        """Create a new category via the service layer."""
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = CategoryService.create_category(
            performed_by=request.user,
            **serializer.validated_data,
        )

        return Response(
            {"category": CategorySerializer(category).data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Full update via service layer."""
        category = self.get_object()
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = CategoryService.update_category(
            performed_by=request.user,
            category=category,
            **serializer.validated_data,
        )

        return Response({"category": CategorySerializer(category).data})

    def partial_update(self, request, *args, **kwargs):
        """Partial update via service layer."""
        category = self.get_object()
        serializer = CategoryWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        category = CategoryService.update_category(
            performed_by=request.user,
            category=category,
            **serializer.validated_data,
        )

        return Response({"category": CategorySerializer(category).data})

    @extend_schema(
        summary="Deactivate Category",
        description="Deactivate a category and cascade to all descendants.",
        request=None,
        responses={200: CategorySerializer},
    )
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        """Deactivate a category (cascades to children)."""
        category = self.get_object()
        category = CategoryService.deactivate_category(
            performed_by=request.user,
            category=category,
        )
        return Response({"category": CategorySerializer(category).data})

    @extend_schema(
        summary="Activate Category",
        description="Re-activate a single category (does not cascade).",
        request=None,
        responses={200: CategorySerializer},
    )
    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """Activate a single category."""
        category = self.get_object()
        category = CategoryService.activate_category(
            performed_by=request.user,
            category=category,
        )
        return Response({"category": CategorySerializer(category).data})
