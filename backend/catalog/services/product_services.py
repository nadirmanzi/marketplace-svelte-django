"""
Business logic for Product and ProductVariant lifecycle operations.

All state mutations flow through these services to keep views thin
and ensure consistent audit logging. Stock adjustments use
SELECT FOR UPDATE to prevent race conditions.

ProductService:
- create_product, update_product, archive_product, publish_product

VariantService:
- create_variant, update_variant, deactivate_variant, activate_variant
- adjust_stock (row-locked via select_for_update)
"""

from django.db import transaction, DatabaseError
from django.db.models import F
from django.core.exceptions import ValidationError as DjangoValidationError
from config.logging import audit_log
from users.exceptions import (
    ConflictError,
    ServiceValidationError,
    NotFoundError,
)

from catalog.models import Product, ProductVariant


class ProductService:
    """
    Encapsulates Product blueprint lifecycle logic.

    All methods are atomic. On success they return the Product instance.
    On failure they raise a ServiceError subclass.
    """

    @classmethod
    @transaction.atomic
    def create_product(cls, *, performed_by, **data) -> Product:
        """
        Create a new product blueprint.

        Args:
            performed_by: The user creating the product (becomes the owner).
            **data: Fields — name, description, base_price, category, status, slug.

        Returns:
            Product: The newly created instance.
        """
        category = data.pop("category", None)
        category_instance = None

        if category:
            category_instance = cls._resolve_category(category)

        try:
            product = Product(
                user=performed_by,
                category=category_instance,
                **data,
            )
            product.save()

            audit_log.info(
                action="product.create",
                message=f"Product created: {product.name} ({product.product_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "product_id": str(product.product_id),
                    "performed_by": str(performed_by.user_id),
                },
            )
            return product

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="product.create",
                message=f"Database error creating product: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def update_product(cls, *, performed_by, product, **data) -> Product:
        """
        Update an existing product blueprint.

        Args:
            performed_by: The user performing the update.
            product: Existing Product instance.
            **data: Fields to update.

        Returns:
            Product: The updated instance.
        """
        category = data.pop("category", None)

        if category is not None:
            if category == "" or category is None:
                product.category = None
            else:
                product.category = cls._resolve_category(category)

        for field, value in data.items():
            if hasattr(product, field):
                setattr(product, field, value)

        try:
            product.save()

            audit_log.info(
                action="product.update",
                message=f"Product updated: {product.name} ({product.product_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "product_id": str(product.product_id),
                    "performed_by": str(performed_by.user_id),
                },
            )
            return product

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="product.update",
                message=f"Database error updating product: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def archive_product(cls, *, performed_by, product) -> Product:
        """
        Archive a product and deactivate all its variants.

        Args:
            performed_by: The user performing the action.
            product: Product instance to archive.

        Returns:
            Product: The updated instance.

        Raises:
            ConflictError: If already archived.
        """
        if product.status == Product.Status.ARCHIVED:
            raise ConflictError("Product is already archived.")

        try:
            product.status = Product.Status.ARCHIVED
            product.save(update_fields=["status", "updated_at"])

            # Cascade: deactivate all variants
            deactivated_count = product.variants.filter(is_active=True).update(
                is_active=False
            )

            audit_log.info(
                action="product.archive",
                message=f"Product archived: {product.name} ({product.product_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "product_id": str(product.product_id),
                    "performed_by": str(performed_by.user_id),
                    "variants_deactivated": deactivated_count,
                },
            )
            return product

        except DatabaseError as e:
            audit_log.error(
                action="product.archive",
                message=f"Database error archiving product: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def publish_product(cls, *, performed_by, product) -> Product:
        """
        Publish/un-archive a product.

        Args:
            performed_by: The user performing the action.
            product: Product instance to publish.

        Returns:
            Product: The updated instance.

        Raises:
            ConflictError: If already published.
        """
        if product.status == Product.Status.PUBLISHED:
            raise ConflictError("Product is already published.")

        try:
            product.status = Product.Status.PUBLISHED
            product.save(update_fields=["status", "updated_at"])

            audit_log.info(
                action="product.publish",
                message=f"Product published: {product.name} ({product.product_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "product_id": str(product.product_id),
                    "performed_by": str(performed_by.user_id),
                },
            )
            return product

        except DatabaseError as e:
            audit_log.error(
                action="product.publish",
                message=f"Database error publishing product: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @staticmethod
    def _resolve_category(category_ref):
        """Resolve a category reference (UUID or instance)."""
        from catalog.models import Category

        if isinstance(category_ref, Category):
            return category_ref
        try:
            return Category.objects.get(pk=category_ref)
        except Category.DoesNotExist:
            raise NotFoundError(f"Category not found: {category_ref}")


class VariantService:
    """
    Encapsulates ProductVariant lifecycle logic and stock management.

    The adjust_stock method uses SELECT FOR UPDATE to acquire a row-level
    lock, preventing race conditions during concurrent stock changes.
    """

    @classmethod
    @transaction.atomic
    def create_variant(cls, *, performed_by, product, **data) -> ProductVariant:
        """
        Create a new variant under a product blueprint.

        Args:
            performed_by: The user creating the variant.
            product: Parent Product instance.
            **data: Fields — sku, name, price, stock_quantity, metadata, is_active.

        Returns:
            ProductVariant: The newly created instance.
        """
        try:
            variant = ProductVariant(product=product, **data)
            variant.save()

            audit_log.info(
                action="variant.create",
                message=f"Variant created: {variant.name} ({variant.variant_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "variant_id": str(variant.variant_id),
                    "product_id": str(product.product_id),
                    "performed_by": str(performed_by.user_id),
                    "sku": variant.sku,
                },
            )
            return variant

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="variant.create",
                message=f"Database error creating variant: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def update_variant(cls, *, performed_by, variant, **data) -> ProductVariant:
        """
        Update an existing variant.

        Args:
            performed_by: The user performing the update.
            variant: Existing ProductVariant instance.
            **data: Fields to update (excluding stock_quantity — use adjust_stock).

        Returns:
            ProductVariant: The updated instance.
        """
        # Stock should only be changed via adjust_stock for safety
        data.pop("stock_quantity", None)

        for field, value in data.items():
            if hasattr(variant, field):
                setattr(variant, field, value)

        try:
            variant.save()

            audit_log.info(
                action="variant.update",
                message=f"Variant updated: {variant.name} ({variant.variant_id})",
                status="success",
                source="catalog.services.product_services",
                extra={
                    "variant_id": str(variant.variant_id),
                    "performed_by": str(performed_by.user_id),
                },
            )
            return variant

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="variant.update",
                message=f"Database error updating variant: {str(e)}",
                status="failed",
                source="catalog.services.product_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def adjust_stock(
        cls, *, performed_by, variant, quantity_delta: int
    ) -> ProductVariant:
        """
        Atomically adjust stock quantity with row-level locking.

        Uses SELECT FOR UPDATE to acquire an exclusive lock on the variant
        row, preventing concurrent modifications from producing incorrect totals.

        Args:
            performed_by: The user performing the adjustment.
            variant: ProductVariant instance (will be re-fetched with lock).
            quantity_delta: Positive to add stock, negative to reduce.

        Returns:
            ProductVariant: The updated instance with new stock_quantity.

        Raises:
            ServiceValidationError: If delta is zero or would result in negative stock.
        """
        if quantity_delta == 0:
            raise ServiceValidationError("Stock adjustment delta cannot be zero.")

        # Acquire row-level lock
        locked_variant = (
            ProductVariant.objects
            .select_for_update()
            .get(pk=variant.pk)
        )

        new_quantity = locked_variant.stock_quantity + quantity_delta
        if new_quantity < 0:
            raise ServiceValidationError(
                f"Insufficient stock. Current: {locked_variant.stock_quantity}, "
                f"requested delta: {quantity_delta}."
            )

        locked_variant.stock_quantity = new_quantity
        locked_variant.save(update_fields=["stock_quantity", "updated_at"])

        audit_log.info(
            action="variant.adjust_stock",
            message=(
                f"Stock adjusted for {locked_variant.sku}: "
                f"{locked_variant.stock_quantity - quantity_delta} → {new_quantity}"
            ),
            status="success",
            source="catalog.services.product_services",
            extra={
                "variant_id": str(locked_variant.variant_id),
                "performed_by": str(performed_by.user_id),
                "sku": locked_variant.sku,
                "delta": quantity_delta,
                "old_quantity": locked_variant.stock_quantity - quantity_delta,
                "new_quantity": new_quantity,
            },
        )
        return locked_variant

    @classmethod
    @transaction.atomic
    def deactivate_variant(cls, *, performed_by, variant) -> ProductVariant:
        """Deactivate a variant."""
        if not variant.is_active:
            raise ConflictError("Variant is already inactive.")

        variant.is_active = False
        variant.save(update_fields=["is_active", "updated_at"])

        audit_log.info(
            action="variant.deactivate",
            message=f"Variant deactivated: {variant.sku} ({variant.variant_id})",
            status="success",
            source="catalog.services.product_services",
            extra={
                "variant_id": str(variant.variant_id),
                "performed_by": str(performed_by.user_id),
            },
        )
        return variant

    @classmethod
    @transaction.atomic
    def activate_variant(cls, *, performed_by, variant) -> ProductVariant:
        """Activate a variant."""
        if variant.is_active:
            raise ConflictError("Variant is already active.")

        variant.is_active = True
        variant.save(update_fields=["is_active", "updated_at"])

        audit_log.info(
            action="variant.activate",
            message=f"Variant activated: {variant.sku} ({variant.variant_id})",
            status="success",
            source="catalog.services.product_services",
            extra={
                "variant_id": str(variant.variant_id),
                "performed_by": str(performed_by.user_id),
            },
        )
        return variant
