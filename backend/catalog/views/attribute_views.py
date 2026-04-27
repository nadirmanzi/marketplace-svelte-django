"""
Views for the attribute management system.

Includes:
- AttributeViewSet: CRUD for attribute definitions.
- CategoryAttributeInfoView: Helper to fetch attributes for a specific category.
"""

from rest_framework import viewsets, permissions, status, response, views
from drf_spectacular.utils import extend_schema, OpenApiParameter
from catalog.models import Attribute, Category
from catalog.serializers import (
    AttributeSerializer,
    CategoryAttributeInfoSerializer,
)
from catalog.services.attribute_services import AttributeService


@extend_schema(tags=["Management - Attributes"])
class AttributeViewSet(viewsets.ModelViewSet):
    """
    Staff-only ViewSet for managing attribute definitions and their options.
    """

    queryset = Attribute.objects.prefetch_related("options").all()
    serializer_class = AttributeSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "slug"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response({"attributes": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response({"attribute": serializer.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"attribute": serializer.data})

    def perform_create(self, serializer):
        # AttributeService handles options creation too if we went that route,
        # but ModelViewSet handle simple cases well.
        serializer.save()


@extend_schema(tags=["Public - Catalog"])
class CategoryAttributeInfoView(views.APIView):
    """
    Return a list of all attributes assigned to a category (including inherited ones).
    Useful for frontends to build dynamic product/variant creation forms.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("category_id", str, OpenApiParameter.PATH, description="UUID of the category"),
        ],
        responses={200: CategoryAttributeInfoSerializer(many=True)},
    )
    def get(self, request, category_id):
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return response.Response(
                {"detail": "Category not found."}, status=status.HTTP_404_NOT_FOUND
            )

        attributes = AttributeService.get_attributes_for_category(category)
        
        # We wrap them in a simple structure that includes ordering info if needed
        # but for now we just return the attributes in order.
        data = []
        for i, attr in enumerate(attributes):
            data.append({
                "attribute": AttributeSerializer(attr).data,
                "order": i
            })
            
        return response.Response({"attributes": data})
