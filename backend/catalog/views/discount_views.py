"""
Discount management API views.
"""

from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from catalog.models import Discount
from catalog.serializers import DiscountSerializer, DiscountWriteSerializer
from catalog.services.discount_services import DiscountService


@extend_schema_view(
    list=extend_schema(summary="List Discounts"),
    retrieve=extend_schema(summary="Get Discount Detail"),
    create=extend_schema(
        summary="Create Discount",
        request=DiscountWriteSerializer,
        responses={201: DiscountSerializer},
    ),
    update=extend_schema(
        summary="Update Discount",
        request=DiscountWriteSerializer,
        responses={200: DiscountSerializer},
    ),
    partial_update=extend_schema(
        summary="Partial Update Discount",
        request=DiscountWriteSerializer,
        responses={200: DiscountSerializer},
    ),
    destroy=extend_schema(summary="Delete Discount", request=None, responses={204: None}),
)
class DiscountManagementViewSet(viewsets.ModelViewSet):
    """
    Staff-only CRUD for discounts via service layer.
    """

    permission_classes = [IsAdminUser]
    serializer_class = DiscountSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Discount.objects.all().prefetch_related("categories", "products", "variants")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DiscountWriteSerializer
        return DiscountSerializer

    def create(self, request, *args, **kwargs):
        serializer = DiscountWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        discount = DiscountService.create_discount(
            performed_by=request.user,
            **serializer.validated_data,
        )
        return Response(DiscountSerializer(discount).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        discount = self.get_object()
        serializer = DiscountWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        discount = DiscountService.update_discount(
            performed_by=request.user,
            discount=discount,
            **serializer.validated_data,
        )
        return Response(DiscountSerializer(discount).data)

    def partial_update(self, request, *args, **kwargs):
        discount = self.get_object()
        serializer = DiscountWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        discount = DiscountService.update_discount(
            performed_by=request.user,
            discount=discount,
            **serializer.validated_data,
        )
        return Response(DiscountSerializer(discount).data)

    def destroy(self, request, *args, **kwargs):
        discount = self.get_object()
        DiscountService.delete_discount(
            performed_by=request.user,
            discount=discount,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
