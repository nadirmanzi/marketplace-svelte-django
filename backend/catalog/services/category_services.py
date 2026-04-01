"""
Business logic for category lifecycle operations.

All state mutations flow through this service to keep views thin
and ensure consistent audit logging. Methods raise typed exceptions
from users.exceptions (handled globally by config/exceptions.py).

Methods:
- create_category: Validate and persist a new category.
- update_category: Partial update with hierarchy validation.
- deactivate_category: Toggle is_active=False (cascades to children).
- activate_category: Toggle is_active=True.
"""

from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError as DjangoValidationError
from config.logging import audit_log
from users.exceptions import (
    ConflictError,
    ServiceValidationError,
    NotFoundError,
)

from catalog.models import Category


class CategoryService:
    """
    Encapsulates category business logic.

    All methods are atomic. On success they return the Category instance.
    On failure they raise a ServiceError subclass.
    """

    @classmethod
    @transaction.atomic
    def create_category(cls, *, performed_by, **data) -> "Category":
        """
        Create a new category.

        Args:
            performed_by: The user performing the action (for audit).
            **data: Fields to set (name, slug, description, image, parent, is_active).

        Returns:
            Category: The newly created instance.

        Raises:
            ServiceValidationError: If validation fails (missing name, circular ref, etc).
        """
        parent = data.pop("parent", None)
        parent_instance = None

        if parent:
            parent_instance = cls._resolve_parent(parent)

        try:
            category = Category(parent=parent_instance, **data)
            category.save()

            audit_log.info(
                action="category.create",
                message=f"Category created: {category.name} ({category.category_id})",
                status="success",
                source="catalog.services.category_services",
                extra={
                    "category_id": str(category.category_id),
                    "performed_by": str(getattr(performed_by, "user_id", performed_by)),
                    "parent_id": str(parent_instance.category_id) if parent_instance else None,
                },
            )
            return category

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="category.create",
                message=f"Database error creating category: {str(e)}",
                status="failed",
                source="catalog.services.category_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def update_category(cls, *, performed_by, category, **data) -> "Category":
        """
        Partially update a category.

        Args:
            performed_by: The user performing the action.
            category: Existing Category instance.
            **data: Fields to update.

        Returns:
            Category: The updated instance.

        Raises:
            ServiceValidationError: On validation failure.
        """
        parent = data.pop("parent", None)

        if parent is not None:
            if parent == "":
                category.parent = None
            else:
                category.parent = cls._resolve_parent(parent)

        update_fields = []
        for field, value in data.items():
            if hasattr(category, field):
                setattr(category, field, value)
                update_fields.append(field)

        try:
            category.save()

            audit_log.info(
                action="category.update",
                message=f"Category updated: {category.name} ({category.category_id})",
                status="success",
                source="catalog.services.category_services",
                extra={
                    "category_id": str(category.category_id),
                    "performed_by": str(getattr(performed_by, "user_id", performed_by)),
                    "updated_fields": update_fields,
                },
            )
            return category

        except DjangoValidationError as e:
            raise ServiceValidationError(
                "; ".join(
                    msg for messages in e.message_dict.values() for msg in messages
                )
            )
        except DatabaseError as e:
            audit_log.error(
                action="category.update",
                message=f"Database error updating category: {str(e)}",
                status="failed",
                source="catalog.services.category_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def deactivate_category(cls, *, performed_by, category) -> "Category":
        """
        Deactivate a category and optionally cascade to its children.

        Args:
            performed_by: The user performing the action.
            category: Category instance to deactivate.

        Returns:
            Category: The updated instance.

        Raises:
            ConflictError: If already inactive.
        """
        if not category.is_active:
            raise ConflictError("Category is already inactive.")

        try:
            category.is_active = False
            category.save(update_fields=["is_active", "updated_at"])

            # Cascade: deactivate all descendants
            descendant_count = cls._cascade_deactivate(category)

            audit_log.info(
                action="category.deactivate",
                message=f"Category deactivated: {category.name} ({category.category_id})",
                status="success",
                source="catalog.services.category_services",
                extra={
                    "category_id": str(category.category_id),
                    "performed_by": str(getattr(performed_by, "user_id", performed_by)),
                    "descendants_deactivated": descendant_count,
                },
            )
            return category

        except DatabaseError as e:
            audit_log.error(
                action="category.deactivate",
                message=f"Database error deactivating category: {str(e)}",
                status="failed",
                source="catalog.services.category_services",
            )
            raise

    @classmethod
    @transaction.atomic
    def activate_category(cls, *, performed_by, category) -> "Category":
        """
        Re-activate a category.

        Note: Does NOT cascade to children. Each child must be
        activated individually to prevent accidental mass-activation.

        Args:
            performed_by: The user performing the action.
            category: Category instance to activate.

        Returns:
            Category: The updated instance.

        Raises:
            ConflictError: If already active.
        """
        if category.is_active:
            raise ConflictError("Category is already active.")

        try:
            category.is_active = True
            category.save(update_fields=["is_active", "updated_at"])

            audit_log.info(
                action="category.activate",
                message=f"Category activated: {category.name} ({category.category_id})",
                status="success",
                source="catalog.services.category_services",
                extra={
                    "category_id": str(category.category_id),
                    "performed_by": str(getattr(performed_by, "user_id", performed_by)),
                },
            )
            return category

        except DatabaseError as e:
            audit_log.error(
                action="category.activate",
                message=f"Database error activating category: {str(e)}",
                status="failed",
                source="catalog.services.category_services",
            )
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_parent(parent_ref) -> "Category":
        """
        Resolve a parent reference (UUID or instance) to a Category.

        Args:
            parent_ref: UUID string, UUID object, or Category instance.

        Returns:
            Category: The resolved parent instance.

        Raises:
            NotFoundError: If the parent UUID does not exist.
        """
        if isinstance(parent_ref, Category):
            return parent_ref

        try:
            return Category.objects.get(pk=parent_ref)
        except Category.DoesNotExist:
            raise NotFoundError(f"Parent category not found: {parent_ref}")

    @staticmethod
    def _cascade_deactivate(category) -> int:
        """
        Recursively deactivate all children of a category.

        Returns the total number of descendants deactivated.
        """
        count = 0
        children = Category.objects.filter(parent=category, is_active=True)
        for child in children:
            child.is_active = False
            child.save(update_fields=["is_active", "updated_at"])
            count += 1
            count += CategoryService._cascade_deactivate(child)
        return count
